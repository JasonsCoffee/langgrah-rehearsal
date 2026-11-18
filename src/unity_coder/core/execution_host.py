"""Narrow file tools for model clients; arbitrary process agents are unsupported."""

from pathlib import Path

from .contracts import Contract
from .ownership import PathRules, confined_path, portable_path, within, validate_owned_path
from .storage import atomic_write
from .workspaces import Workspace


class ExecutionHost:
    def __init__(self, workspace: Workspace, contract: Contract, rules: PathRules, *,
                 mode: str = "mediated-tools", frozen_paths: tuple[str, ...] = (),
                 approved_reads: tuple[str, ...] = ()) -> None:
        if mode != "mediated-tools" or workspace.kind != "unit" or workspace.unit_id is None:
            raise ValueError("Unsupported isolation: model must use mediated file tools only")
        self.workspace, self.contract, self.rules = workspace, contract, rules
        self.frozen_paths = frozen_paths
        self.read_scopes = (contract.module_root,) + contract.test_roots + approved_reads + (
            contract.spec.path, contract.presentation_ref.path, contract.coding_profile_ref.path, contract.environment_ref.path)

    def _path(self, path: str) -> Path:
        portable_path(path)
        target = confined_path(self.workspace.path, path)
        for spelling in (path, target.relative_to(self.workspace.path).as_posix()):
            if any(self.rules.normalise_path(part) in (self.rules.normalise_path(".git"), self.rules.normalise_path(".agent")) for part in spelling.split("/")):
                raise ValueError("Shared metadata and coordinator state are inaccessible")
        return target

    def write_file(self, path: str, content: bytes) -> None:
        self._path(path)
        unit = next(u for u in self.contract.units if u.id == self.workspace.unit_id)
        validate_owned_path(path, (self.contract.module_root,) if unit.role == "impl" else self.contract.test_roots,
                            self.workspace.path, self.rules, self.frozen_paths)
        if self.contract.owner_of(path) != self.workspace.unit_id or any(within(path, p, self.rules) for p in self.frozen_paths):
            raise ValueError("Tool write is outside unit ownership or changes frozen content")
        atomic_write(self.workspace.path, path, content)

    def read_file(self, path: str) -> bytes:
        target = self._path(path)
        if not any(within(path, p, self.rules) for p in self.read_scopes):
            raise ValueError("Read is outside approved context")
        return target.read_bytes()

    def run_command(self, command: list[str]) -> None:
        raise ValueError("Arbitrary commands, Git, network, and editor access are not coding tools")
