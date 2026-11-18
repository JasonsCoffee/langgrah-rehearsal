"""Manifest-bound synchronization of one game into a dedicated Unity host."""

from collections.abc import Callable, Mapping
from hashlib import sha256
import json
from pathlib import Path

from . import UnityAdapter
from ...core.ownership import confined_path, portable_path, within
from ...core.storage import atomic_write, file_guard


def _hashes(files: Mapping[str, bytes]) -> dict[str, str]:
    return {path: sha256(content).hexdigest() for path, content in files.items()}


class CandidateHost:
    """Worker-only interface; caller retains the host lease through all gates.

    A new host requires an empty game mount. Interrupted synchronization fails
    closed until controlled reprovisioning; it never adopts arbitrary leftovers.
    """

    _state = ".agent/materialization.json"

    def __init__(self, root: Path, mount: str, *, assembly: str,
                 dependencies: Mapping[str, str], probe: Callable[[], Mapping[str, str]],
                 operational_roots: tuple[str, ...] = ("Library", "Logs", "Temp")) -> None:
        self.root = root.resolve()
        self.rules = UnityAdapter()
        self.mount = portable_path(mount)
        if not mount.startswith("Assets/"):
            raise ValueError("Game mount must be under Assets")
        self.game = confined_path(self.root, mount)
        self._check_mount()
        if not all((self.root / p).is_dir() for p in ("Assets", "Packages", "ProjectSettings")):
            raise ValueError("Complete Unity host required")
        self.assembly = assembly
        self.dependencies = dict(dependencies)
        self.probe = probe
        for path in operational_roots:
            portable_path(path)
            if any(within(path, protected, self.rules) for protected in
                   ("Assets", "Packages", "ProjectSettings", ".git", ".agent")):
                raise ValueError("Operational output overlaps protected host")
        self.outputs = operational_roots

    def _check_mount(self) -> None:
        current = self.root
        for component in self.mount.split("/"):
            current /= component
            if current.is_symlink() or current.is_junction():
                raise ValueError("Game mount must not contain aliases")
        if confined_path(self.root, self.mount) != self.game:
            raise ValueError("Game mount changed")

    def _scan(self, root: Path, *, host: bool = False) -> dict[str, bytes]:
        files: dict[str, bytes] = {}
        if not root.exists():
            return files
        def visit(directory: Path) -> None:
            for entry in directory.iterdir():
                relative = entry.relative_to(root).as_posix()
                if host and (within(relative, self.mount, self.rules)
                             or any(within(relative, p, self.rules)
                                    for p in (*self.outputs, ".agent", ".git"))):
                    continue
                if entry.is_symlink() or entry.is_junction():
                    raise ValueError(f"Linked host path: {relative}")
                confined_path(root, relative)
                if entry.is_dir():
                    visit(entry)
                else:
                    files[relative] = entry.read_bytes()
        visit(root)
        return files

    def _read(self) -> dict:
        path = confined_path(self.root, self._state)
        if not path.exists():
            return {}
        state = json.loads(path.read_bytes())
        if state["mount"] != self.mount or state["assembly"] != self.assembly or state["dependencies"] != self.dependencies:
            raise ValueError("Host provisioning identity changed")
        if state.get("installing"):
            raise ValueError("Interrupted materialization requires controlled reprovisioning")
        return state

    def _write(self, state: dict) -> None:
        atomic_write(self.root, self._state, json.dumps(state, sort_keys=True).encode())

    def _host(self, state: dict) -> dict[str, str]:
        self._check_mount()
        if dict(self.probe()) != self.dependencies:
            raise ValueError("Dependency revision drift")
        host = _hashes(self._scan(self.root, host=True))
        if state and host != state["host"]:
            raise ValueError("Host drift; controlled reprovisioning required")
        return host

    def _validate(self, files: Mapping[str, bytes]) -> None:
        keys: set[str] = set()
        for path in files:
            confined_path(self.game, path)
            if any(part.startswith(".git") or part == ".agent" for part in path.split("/")):
                raise ValueError("Candidate contains execution metadata")
            key = self.rules.normalise_path(path)
            if key in keys:
                raise ValueError("Candidate path collision")
            keys.add(key)
        for key in keys:
            if any(key.startswith(other + "/") for other in keys):
                raise ValueError("Candidate file/directory collision")
        for path in files:
            if path.endswith(".meta"):
                base = path[:-5]
                if base not in files and not any(p.startswith(base + "/") for p in files):
                    raise ValueError("Orphan metadata")
        assemblies = [p for p, data in files.items()
                      if p.endswith(".asmdef") and json.loads(data).get("name") == self.assembly]
        outside = self._scan(self.root, host=True)
        assemblies.extend(p for p, data in outside.items()
                          if p.startswith("Assets/") and p.endswith(".asmdef")
                          and json.loads(data).get("name") == self.assembly)
        if len(assemblies) != 1:
            raise ValueError("Assembly must have exactly one game mount")

    def materialize(self, candidate: str, files: Mapping[str, bytes]) -> None:
        """Install a complete snapshot; remove only previous manifest entries."""
        if not candidate:
            raise ValueError("Candidate identity required")
        snapshot = dict(files)
        with file_guard(self.root, ".agent/materialization.guard"):
            state = self._read()
            host = self._host(state)
            self._validate(snapshot)
            current = _hashes(self._scan(self.game))
            expected = dict(state.get("files", {}))
            expected.update(state.get("pending", {}))
            if current != expected:
                raise ValueError("Unmanaged or changed game content")
            hashes = _hashes(snapshot)
            history = dict(state.get("history", {}))
            if candidate in history and history[candidate] != hashes:
                raise ValueError("Candidate identity reused for different content")
            for path, digest in state.get("pending", {}).items():
                if hashes.get(path) != digest or candidate == state["candidate"]:
                    raise ValueError("Import metadata requires a reconciled candidate")
            history[candidate] = hashes
            next_state = dict(mount=self.mount, assembly=self.assembly,
                              dependencies=self.dependencies, host=host, files=hashes,
                              candidate=candidate, pending={}, history=history, installing=True)
            self._write(next_state)
            for path in set(expected) - set(snapshot):
                confined_path(self.game, path).unlink()
            for path, content in snapshot.items():
                atomic_write(self.game, path, content)
            next_state["installing"] = False
            self._write(next_state)

    def capture_import(self, candidate: str) -> dict[str, bytes]:
        """Capture only new sidecars; commit them before another request."""
        with file_guard(self.root, ".agent/materialization.guard"):
            state = self._read()
            self._host(state)
            if state.get("candidate") != candidate:
                raise ValueError("Stale import candidate")
            files = self._scan(self.game)
            hashes = _hashes(files)
            for path, digest in state["files"].items():
                if hashes.get(path) != digest:
                    raise ValueError("Import modified frozen candidate content")
            added = {p: data for p, data in files.items() if p not in state["files"]}
            if any(not p.endswith(".meta") for p in added):
                raise ValueError("Import generated non-metadata content")
            self._validate(files)
            if state.get("pending") and state["pending"] != _hashes(added):
                raise ValueError("Pending metadata changed")
            state["pending"] = _hashes(added)
            self._write(state)
            return added

    def assert_ready(self, candidate: str) -> None:
        """Call around every gate while retaining exclusive host access."""
        with file_guard(self.root, ".agent/materialization.guard"):
            state = self._read()
            self._host(state)
            if state.get("candidate") != candidate or state.get("pending"):
                raise ValueError("Candidate is stale or needs import reconciliation")
            files = self._scan(self.game)
            if _hashes(files) != state["files"]:
                raise ValueError("Candidate content drift")
            self._validate(files)
