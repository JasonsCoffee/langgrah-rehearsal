"""Confined atomic artifact writes shared by durable execution components."""

import os
from pathlib import Path
import tempfile
import time
from contextlib import contextmanager
from collections.abc import Iterator

from .ownership import confined_path


@contextmanager
def file_guard(root: Path, relative: str) -> Iterator[None]:
    """OS-owned advisory guard; a dead process cannot retain this lock."""
    path = confined_path(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def atomic_write(root: Path, relative: str, content: bytes) -> None:
    target = confined_path(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".write-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        # Recheck confinement immediately before publishing the artifact.
        if confined_path(root, relative) != target:
            raise ValueError("Artifact target changed during write")
        deadline = time.monotonic() + 2.0
        while True:
            try:
                os.replace(temporary, target)
                break
            except PermissionError as exc:
                # Windows readers/scanners may briefly deny rename. Never
                # truncate the visible file or retry permanent errors forever.
                if getattr(exc, "winerror", None) not in (5, 32, 33) or time.monotonic() >= deadline:
                    raise
                time.sleep(0.01)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
