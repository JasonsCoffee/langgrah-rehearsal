"""Coordinator-owned external module worktrees and checked candidate integration."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from types import MappingProxyType
from typing import Literal, Mapping

from .contracts import Contract
from .ownership import PathRules, confined_path, validate_owned_path
from .storage import atomic_write


@dataclass(frozen=True)
class Workspace:
    path: Path
    branch: str
    kind: Literal["unit", "integration"]
    base_revision: str
    unit_id: str | None
    dependencies: Mapping[str, str]


@dataclass(frozen=True)
class WorkspaceCandidate:
    unit_id: str
    contract_sha256: str
    base_revision: str
    dependencies: Mapping[str, str]
    changes: Mapping[str, bytes | None]


def git(repository: Path, *arguments: str) -> bytes:
    """Use argument arrays, never compose executable shell text from paths."""
    result = subprocess.run(["git", "-C", str(repository), *arguments], capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"Git operation failed ({arguments[0]}): {result.stderr.decode('utf-8', errors='replace').strip()}")
    return result.stdout


def _identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value):
        raise ValueError("Unsafe workspace identifier")
    return value


class WorkspaceManager:
    def __init__(self, repository: Path, workspace_root: Path, contract: Contract, rules: PathRules, *,
                 run_id: str, imported_roots: tuple[Path, ...], frozen_paths: tuple[str, ...] = ()) -> None:
        self.repository = repository.resolve()
        self.workspace_root = workspace_root.resolve()
        self.contract, self.rules, self.run_id = contract, rules, _identifier(run_id)
        self.frozen_paths = frozen_paths
        if (self.workspace_root.is_relative_to(self.repository) or self.repository.is_relative_to(self.workspace_root)
            or any(self.workspace_root.is_relative_to(p.resolve()) for p in imported_roots)):
            raise ValueError("Coding workspaces must be external to repository and imported trees")
        actual_root = Path(git(repository, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        if actual_root != self.repository:
            raise ValueError("Configured module is not an independent repository root")
        self._handles: dict[Path, Workspace] = {}

    def _create(self, name: str, branch: str, kind: Literal["unit", "integration"], base: str,
                unit_id: str | None, dependencies: Mapping[str, str]) -> Workspace:
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", base):
            raise ValueError("Workspace baseline must be an identified commit")
        git(self.repository, "cat-file", "-e", base + "^{commit}")
        path = confined_path(self.workspace_root, self.run_id + "/" + name)
        if path.exists():
            raise ValueError("Workspace location already exists; reconcile before reuse")
        path.parent.mkdir(parents=True, exist_ok=True)
        # Frozen hashes describe committed bytes, not workstation newline policy.
        # Command-local settings leave the user's repository configuration intact.
        git(self.repository, "-c", "core.autocrlf=false", "-c", "core.eol=lf",
            "worktree", "add", "-b", branch, str(path), base)
        handle = Workspace(path, branch, kind, base, unit_id, MappingProxyType(dict(dependencies)))
        self._handles[path] = handle
        return handle

    def create_unit(self, unit_id: str, base_revision: str, dependencies: Mapping[str, str]) -> Workspace:
        _identifier(unit_id)
        unit = next((u for u in self.contract.units if u.id == unit_id and u.status == "active"), None)
        if unit is None or set(dependencies) != set(unit.depends_on):
            raise ValueError("Workspace needs exact declared dependency revisions")
        version = self.contract.contract_version
        return self._create(f"unit-v{version}-{unit_id}", f"agent/{self.run_id}/unit-v{version}-{unit_id}",
                            "unit", base_revision, unit_id, dependencies)

    def create_integration(self, version: int, base_revision: str) -> Workspace:
        if version != self.contract.contract_version:
            raise ValueError("Integration version differs from contract")
        return self._create(f"integration-v{version}", f"agent/{self.run_id}/cycle-{version}",
                            "integration", base_revision, None, {})

    def reopen_unit(self, unit_id: str, base: str, dependencies: Mapping[str,str]) -> Workspace:
        _identifier(unit_id)
        path=confined_path(self.workspace_root,self.run_id+f"/unit-v{self.contract.contract_version}-{unit_id}")
        branch=f"agent/{self.run_id}/unit-v{self.contract.contract_version}-{unit_id}"
        expected=(self.repository/git(self.repository,'rev-parse','--git-common-dir').decode().strip()).resolve()
        actual=(path/git(path,'rev-parse','--git-common-dir').decode().strip()).resolve()
        if actual!=expected or git(path,'rev-parse','HEAD').decode().strip()!=base:
            raise ValueError('Recovered unit workspace identity changed')
        handle=Workspace(path,branch,'unit',base,unit_id,MappingProxyType(dict(dependencies)))
        self._handles[path]=handle
        self._assert_handle(handle,'unit')
        return handle

    def reopen_integration(self, version: int, base_revision: str) -> Workspace:
        """Reattach only the clean managed branch in this repository's worktree."""
        if version != self.contract.contract_version or not re.fullmatch(r"[0-9a-fA-F]{40,64}",base_revision):
            raise ValueError("Invalid integration recovery identity")
        path = confined_path(self.workspace_root,self.run_id + f"/integration-v{version}")
        branch = f"agent/{self.run_id}/cycle-{version}"
        if git(path,"branch","--show-current").decode().strip() != branch:
            raise ValueError("Managed integration branch changed")
        common = (path / git(path,"rev-parse","--git-common-dir").decode().strip()).resolve()
        expected = (self.repository / git(self.repository,"rev-parse","--git-common-dir").decode().strip()).resolve()
        if common != expected or Path(git(path,"rev-parse","--show-toplevel").decode().strip()).resolve() != path:
            raise ValueError("Integration belongs to another repository")
        if git(path,"status","--porcelain"):
            raise ValueError("Dirty integration requires effect reconciliation")
        git(path,"merge-base","--is-ancestor",base_revision,"HEAD")
        handle = Workspace(path,branch,"integration",base_revision,None,MappingProxyType({}))
        self._handles[path] = handle
        return handle

    def _assert_handle(self, handle: Workspace, kind: str) -> None:
        if self._handles.get(handle.path) != handle or handle.kind != kind:
            raise ValueError("Workspace is not owned by this coordinator for this operation")
        if git(handle.path, "branch", "--show-current").decode().strip() != handle.branch:
            raise ValueError("Managed branch changed")

    def _validate_changes(self, unit_id: str, changes: Mapping[str, bytes | None], root: Path) -> None:
        unit = next((u for u in self.contract.units if u.id == unit_id and u.status == "active"), None)
        if unit is None:
            raise ValueError("Unknown candidate unit")
        protected = self.frozen_paths + (self.contract.spec.path, self.contract.presentation_ref.path,
                                         self.contract.coding_profile_ref.path, self.contract.environment_ref.path)
        for path in changes:
            validate_owned_path(path, (self.contract.module_root,) if unit.role == "impl" else self.contract.test_roots,
                                root, self.rules, protected)
            if not self.rules.is_generated(path) and self.contract.owner_of(path) != unit_id:
                raise ValueError("Candidate changes unowned file")

    def capture(self, handle: Workspace) -> WorkspaceCandidate:
        self._assert_handle(handle, "unit")
        if git(handle.path, "rev-parse", "HEAD").decode().strip() != handle.base_revision:
            raise ValueError("Unit changed shared Git state or baseline")
        records = git(handle.path, "status", "--porcelain=v1", "-z", "--untracked-files=all").decode("utf-8").split("\0")
        paths: set[str] = set()
        index = 0
        while index < len(records):
            record = records[index]
            index += 1
            if not record:
                continue
            paths.add(record[3:])
            if "R" in record[:2] or "C" in record[:2]:
                paths.add(records[index])
                index += 1
        changes: dict[str, bytes | None] = {}
        for path in sorted(paths):
            target = confined_path(handle.path, path)
            changes[path] = target.read_bytes() if target.is_file() else None
        assert handle.unit_id is not None
        self._validate_changes(handle.unit_id, changes, handle.path)
        return WorkspaceCandidate(handle.unit_id, self.contract.sha256, handle.base_revision,
                                  handle.dependencies, MappingProxyType(changes))

    def integrate(self, integration: Workspace, candidate: WorkspaceCandidate,
                  current_dependencies: Mapping[str, str]) -> str:
        self._assert_handle(integration, "integration")
        if candidate.contract_sha256 != self.contract.sha256 or dict(candidate.dependencies) != dict(current_dependencies):
            raise ValueError("Stale candidate contract or dependencies")
        self._validate_changes(candidate.unit_id, candidate.changes, integration.path)
        if git(integration.path, "status", "--porcelain"):
            raise ValueError("Integration workspace is dirty; reconcile before applying")
        git(integration.path, "merge-base", "--is-ancestor", candidate.base_revision, "HEAD")
        paths = tuple(candidate.changes)
        if not paths:
            return git(integration.path, "rev-parse", "HEAD").decode().strip()
        if git(integration.path, "diff", "--name-only", candidate.base_revision, "HEAD", "--", *paths):
            raise ValueError("Candidate ownership changed since its base")
        before = git(integration.path, "rev-parse", "HEAD").decode().strip()
        old = {p: confined_path(integration.path, p).read_bytes() if confined_path(integration.path, p).is_file() else None for p in paths}
        if all(old[path] == content for path, content in candidate.changes.items()):
            return before
        try:
            for path, content in candidate.changes.items():
                if content is None:
                    confined_path(integration.path, path).unlink(missing_ok=True)
                else:
                    atomic_write(integration.path, path, content)
            git(integration.path, "add", "--", *paths)
            git(integration.path, "-c", "core.hooksPath=", "commit", "-m", f"Integrate {candidate.unit_id}")
        except Exception:
            git(integration.path, "reset", "--mixed", before)
            for path, content in old.items():
                if content is None:
                    confined_path(integration.path, path).unlink(missing_ok=True)
                else:
                    atomic_write(integration.path, path, content)
            raise
        return git(integration.path, "rev-parse", "HEAD").decode().strip()
