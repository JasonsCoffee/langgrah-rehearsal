"""Rehearsal-only additive overlay. Hold the host lease around every call."""

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.ownership import confined_path, portable_path
from unity_coder.core.storage import atomic_write, file_guard


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


class TrustedOverlay:
    ENTRY_PATH = "Assets/JJGame/monopoly/Runtime/Script/Monopoly.cs"

    def __init__(self, host: Path, state: Path, roots: tuple[str, ...]) -> None:
        self.host = host.resolve(strict=True)
        self.state = state.resolve()
        if self.state == self.host or self.host in self.state.parents:
            raise ValueError("Overlay state must be outside the Unity host")
        self.roots = tuple(portable_path(root) for root in roots)
        if not self.roots or any(not root.startswith("Assets/JJGame/monopoly/") for root in self.roots):
            raise ValueError("Overlay roots must stay inside the authorized game mount")
        for root in self.roots:
            confined_path(self.host, root)
        for name in ("Assets", "Packages", "ProjectSettings"):
            directory = self.host / name
            if not directory.is_dir() or directory.is_symlink() or directory.is_junction():
                raise ValueError("Complete Unity host required")

    def scan(self) -> dict[str, str]:
        paths: list[Path] = []

        def visit(directory: Path) -> None:
            for entry in directory.iterdir():
                if entry.name == ".git":
                    continue
                relative = entry.relative_to(self.host).as_posix()
                if entry.is_symlink() or entry.is_junction():
                    raise ValueError("Linked imported path: " + relative)
                # Every traversed directory is checked before recursion. Avoid
                # resolving the full ancestor chain again for every asset.
                if entry.is_dir():
                    visit(entry)
                else:
                    paths.append(entry)

        for name in ("Assets", "Packages", "ProjectSettings"):
            directory = self.host / name
            if directory.is_symlink() or directory.is_junction():
                raise ValueError("Linked protected root")
            visit(directory)
        def identity(path: Path) -> tuple[str, str]:
            # Recheck links after enumeration before opening bytes. No timestamp
            # cache or exclusions: every protected file is hashed on every scan.
            if path.is_symlink() or path.is_junction():
                raise ValueError("Linked imported path: " + path.relative_to(self.host).as_posix())
            return path.relative_to(self.host).as_posix(), digest(path.read_bytes())

        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="overlay-hash") as pool:
            return dict(pool.map(identity, paths))

    def allowed(self, path: str) -> bool:
        return (any(path == root + ".meta" or path.startswith(root + "/") for root in self.roots)
                or path == self.ENTRY_PATH and path in self.entry_exceptions())

    def entry_exceptions(self) -> dict[str, str]:
        path = self.state / "entry-exceptions.json"
        if not path.exists():
            return {}
        record = json.loads(path.read_bytes())
        baseline = json.loads((self.state / "overlay.json").read_bytes())
        exceptions = record["files"]
        if (record["baseline_sha256"] != baseline["baseline_sha256"]
                or set(exceptions) != {self.ENTRY_PATH}
                or exceptions[self.ENTRY_PATH] != baseline["baseline"].get(self.ENTRY_PATH)):
            raise ValueError("Entry exception identity changed")
        return exceptions

    def register_entry(self, original_sha256: str) -> None:
        """Trusted operator action for the user's existing-entry replacement."""
        with file_guard(self.state, "overlay.guard"):
            value = self.read()
            original = value["baseline"].get(self.ENTRY_PATH)
            if not original or original != original_sha256:
                raise ValueError("Entry original hash differs from baseline")
            if digest(confined_path(self.host, self.ENTRY_PATH).read_bytes()) != original:
                raise ValueError("Original entry bytes drifted before registration")
            prior = self.entry_exceptions()
            if prior:
                return
            atomic_write(self.state, "entry-exceptions.json", json.dumps({
                "baseline_sha256": value["baseline_sha256"],
                "files": {self.ENTRY_PATH: original},
                "authorization": "User selected replacement of the existing Monopoly Game/Scene entry"
            }, sort_keys=True).encode())

    def read(self) -> dict:
        value = json.loads((self.state / "overlay.json").read_bytes())
        if value["roots"] != list(self.roots):
            raise ValueError("Overlay scope changed")
        if value.get("installing"):
            raise ValueError("Interrupted overlay requires explicit reconciliation")
        return value

    def save(self, value: dict) -> None:
        atomic_write(self.state, "overlay.json", json.dumps(value, sort_keys=True).encode())

    def capture_baseline(self) -> str:
        with file_guard(self.state, "overlay.guard"):
            if (self.state / "overlay.json").exists():
                raise ValueError("Baseline already captured")
            files = self.scan()
            if any(self.allowed(path) for path in files):
                raise ValueError("New overlay roots already contain files")
            identity = digest(json.dumps(files, sort_keys=True).encode())
            self.save(dict(roots=self.roots, baseline=files, baseline_sha256=identity,
                           managed={}, candidate=None, history={}, pending={}))
            return identity

    def check(self, value: dict, *, permit_metadata: bool = False) -> dict[str, str]:
        actual = self.scan()
        expected = value["baseline"] | value["managed"] | value["pending"]
        changed = [path for path, identity in expected.items() if actual.get(path) != identity]
        if changed:
            raise ValueError("Baseline or candidate bytes drifted: " + ", ".join(changed[:10]))
        added = {path: identity for path, identity in actual.items() if path not in expected}
        if added and (not permit_metadata or any(not self.allowed(path) or not path.endswith(".meta") for path in added)):
            raise ValueError("Unmanaged import additions")
        return added

    def materialize(self, candidate: str, files: Mapping[str, bytes]) -> None:
        if not candidate or not files:
            raise ValueError("Candidate identity and files required")
        for path, content in files.items():
            portable_path(path)
            confined_path(self.host, path)
            if not self.allowed(path) or not isinstance(content, bytes):
                raise ValueError("Candidate exceeds overlay scope")
            if any(part.startswith(".") for part in path.split("/")):
                raise ValueError("Hidden execution files are forbidden")
        hashes = {path: digest(content) for path, content in files.items()}
        rules = UnityAdapter()
        if len({rules.normalise_path(path) for path in files}) != len(files):
            raise ValueError("Candidate contains path aliases")
        with file_guard(self.state, "overlay.guard"):
            value = self.read()
            self.check(value)
            if (set(files) & value["baseline"].keys()) - self.entry_exceptions().keys():
                raise ValueError("Candidate overlaps protected baseline")
            if not value["managed"].keys() <= files.keys():
                raise ValueError("Overlay cannot remove existing candidate files")
            if any(hashes.get(path) != identity for path, identity in value["pending"].items()):
                raise ValueError("Imported metadata must be adopted verbatim")
            if value["pending"] and candidate == value["candidate"]:
                raise ValueError("Import reconciliation needs a new candidate identity")
            history = value["history"]
            if candidate in history and history[candidate] != hashes:
                raise ValueError("Candidate identity reused")
            value["installing"] = True
            self.save(value)
            for path, content in files.items():
                if value["managed"].get(path) != hashes[path] and value["pending"].get(path) != hashes[path]:
                    atomic_write(self.host, path, content)
            value.update(managed=hashes, pending={}, candidate=candidate, installing=False)
            history[candidate] = hashes
            self.save(value)
            self.check(value)

    def capture_import(self, candidate: str) -> dict[str, bytes]:
        with file_guard(self.state, "overlay.guard"):
            value = self.read()
            if value["candidate"] != candidate:
                raise ValueError("Stale import candidate")
            added = self.check(value, permit_metadata=True)
            for path in added:
                base = path[:-5]
                if base not in value["managed"] and not any(p.startswith(base + "/") for p in value["managed"]):
                    raise ValueError("Orphan imported metadata")
            value["pending"].update(added)
            self.save(value)
            return {path: confined_path(self.host, path).read_bytes() for path in value["pending"]}

    def capture_preparation(self, candidate: str, declared_assets: tuple[str, ...]) -> dict[str, bytes]:
        """Adopt enumerated new editor assets before the presentation freezes."""
        permitted = {portable_path(path) for path in declared_assets}
        suffixes = {".unity", ".prefab", ".asset", ".mat", ".anim", ".controller", ".meta", ".png"}
        if any(not self.allowed(path) or Path(path).suffix not in suffixes for path in permitted):
            raise ValueError("Preparation contains an undeclared asset type or scope")
        with file_guard(self.state, "overlay.guard"):
            value = self.read()
            if value["candidate"] != candidate or value["pending"]:
                raise ValueError("Stale preparation candidate")
            actual = self.scan()
            expected = value["baseline"] | value["managed"]
            if any(actual.get(path) != identity for path, identity in expected.items()):
                raise ValueError("Preparation modified existing source or assets")
            added = {path: identity for path, identity in actual.items() if path not in expected}
            if not added or set(added) != permitted:
                raise ValueError("Prepared assets differ from declared inventory")
            receipt = {"candidate": candidate, "files": added,
                       "baseline_sha256": value["baseline_sha256"]}
            token = digest(json.dumps(receipt, sort_keys=True).encode())
            atomic_write(self.state, "preparations/" + token + ".json", json.dumps(receipt).encode())
            value["pending"] = added
            self.save(value)
            return {path: confined_path(self.host, path).read_bytes() for path in added}

    def assert_ready(self, candidate: str) -> None:
        with file_guard(self.state, "overlay.guard"):
            value = self.read()
            if value["candidate"] != candidate or value["pending"]:
                raise ValueError("Candidate awaits import reconciliation")
            self.check(value)
