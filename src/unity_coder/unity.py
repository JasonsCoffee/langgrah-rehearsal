"""Unity batchmode verification.

Verification is the throughput ceiling of the whole pipeline, and ``Library/``
is single-writer, so every run is wrapped in an exclusive project lock.

Two failure modes are handled explicitly:

1. Compilation fails  -> ``-executeMethod`` never runs, no result file is
   produced. We fall back to scraping ``error CS`` lines from the log.
2. Tests fail          -> the C# verifier writes a JSON result file.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from .state import VerifyResult

COMPILE_ERROR = re.compile(
    r"(?P<file>[^\s:()]+\.cs)\((?P<line>\d+),(?P<col>\d+)\):\s*error\s+(?P<code>CS\d+):\s*(?P<msg>.+)"
)

DEFAULT_TIMEOUT_S = 1800
MAX_ERRORS = 25


class ProjectLocked(RuntimeError):
    """Raised when another verification run holds the project lock."""


def parse_compile_errors(log_text: str) -> list[str]:
    """Extract de-duplicated, human-readable compiler errors from a Unity log."""
    seen: set[str] = set()
    errors: list[str] = []
    for match in COMPILE_ERROR.finditer(log_text):
        entry = (
            f"{os.path.basename(match.group('file'))}:{match.group('line')} "
            f"[{match.group('code')}] {match.group('msg').strip()}"
        )
        if entry not in seen:
            seen.add(entry)
            errors.append(entry)
        if len(errors) >= MAX_ERRORS:
            break
    return errors


class ProjectLock:
    """Exclusive lock file in the Unity project root.

    Deliberately simple: an atomically created sentinel with a stale-age
    escape hatch so a killed run cannot wedge the pipeline forever.
    """

    def __init__(self, project_root: str | Path, stale_after_s: int = 3600):
        self.path = Path(project_root) / ".unity_coder.lock"
        self.stale_after_s = stale_after_s

    def __enter__(self) -> "ProjectLock":
        deadline = time.time() + 300
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                age = time.time() - self.path.stat().st_mtime
                if age > self.stale_after_s:
                    self.path.unlink(missing_ok=True)
                    continue
                if time.time() > deadline:
                    raise ProjectLocked(
                        f"another run holds {self.path} (age {age:.0f}s). "
                        "Wait for it or delete the lock if the process is gone."
                    )
                time.sleep(2)

    def __exit__(self, *exc_info) -> None:
        self.path.unlink(missing_ok=True)


def find_unity_exe(explicit: str | None = None) -> str:
    """Resolve Unity.exe without embedding a machine-specific path.

    Order: explicit argument, UNITY_EXE, UNITY_HUB_ROOT, then
    %PROGRAMFILES%/Unity/Hub/Editor.

    The fallback picks lexicographically, which is not "newest" once you hold more
    than one version. Set UNITY_EXE explicitly whenever the project pins a version.
    """
    if explicit:
        return explicit

    env = os.environ.get("UNITY_EXE")
    if env:
        return env

    hub = os.environ.get("UNITY_HUB_ROOT")
    if not hub:
        program_files = os.environ.get("PROGRAMFILES") or os.environ.get("ProgramFiles")
        if program_files:
            hub = str(Path(program_files) / "Unity" / "Hub" / "Editor")
    if hub:
        candidates = sorted(Path(hub).glob("*/Editor/Unity.exe"), reverse=True)
        if candidates:
            return str(candidates[0])

    raise RuntimeError(
        "Unity executable not found. Set UNITY_EXE (full path to Unity.exe) or "
        "UNITY_HUB_ROOT (defaults to %PROGRAMFILES%/Unity/Hub/Editor) in .env"
    )


def run_verify(
    project_root: str | Path,
    unity_exe: str | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> VerifyResult:
    root = Path(project_root)
    if not (root / "Assets").is_dir():
        raise RuntimeError(f"{root} does not look like a Unity project (no Assets/ directory)")

    temp = root / "Temp"
    temp.mkdir(exist_ok=True)
    result_path = temp / "unity_coder_result.json"
    log_path = temp / "unity_coder_verify.log"
    result_path.unlink(missing_ok=True)

    cmd = [
        find_unity_exe(unity_exe),
        "-batchmode",
        "-nographics",
        "-quit",
        "-projectPath",
        str(root),
        "-executeMethod",
        "UnityCoder.UnityCoderVerifier.Verify",
        "-unityCoderResult",
        str(result_path),
        "-logFile",
        str(log_path),
    ]

    started = time.time()
    with ProjectLock(root):
        try:
            subprocess.run(cmd, capture_output=True, timeout=timeout_s, check=False)
        except subprocess.TimeoutExpired:
            return VerifyResult(
                compiled=False,
                compile_errors=[f"verification exceeded {timeout_s}s and was killed"],
                tests_total=0,
                tests_failed=0,
                failing_tests=[],
                duration_s=round(time.time() - started, 1),
            )

    elapsed = round(time.time() - started, 1)

    if result_path.exists():
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        return VerifyResult(
            compiled=True,
            compile_errors=[],
            tests_total=int(payload.get("tests_total", 0)),
            tests_failed=int(payload.get("tests_failed", 0)),
            failing_tests=list(payload.get("failing_tests", [])),
            duration_s=elapsed,
        )

    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    errors = parse_compile_errors(log_text)
    if not errors:
        errors = ["verification produced no result file and no compile errors; inspect Temp/unity_coder_verify.log"]
    return VerifyResult(
        compiled=False,
        compile_errors=errors,
        tests_total=0,
        tests_failed=0,
        failing_tests=[],
        duration_s=elapsed,
    )
