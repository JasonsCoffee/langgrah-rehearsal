"""Run-owned leases and structured interruption/completion boundaries."""

import json
from pathlib import Path
from typing import Callable

from .contracts import _object, _text
from .journal import run_prefix
from .ownership import confined_path
from .storage import atomic_write, file_guard


class RunLease:
    def __init__(self, root: Path, run_id: str, owner: str) -> None:
        run_prefix(run_id)
        if not owner:
            raise ValueError("Lease needs an owner identity")
        self.root, self.run_id, self.owner = root, run_id, owner
        self._held = False

    def acquire(self, *, owner_alive: Callable[[str], bool], reclaim_stale: bool = False) -> None:
        with file_guard(self.root, ".agent/lease.guard"):
            path = confined_path(self.root, ".agent/run.lock")
            if path.exists():
                prior = _object(json.loads(path.read_bytes()))
                if prior.get("run_id") == self.run_id and prior.get("owner") == self.owner and self._held:
                    return
                if owner_alive(_text(prior.get("owner"))) or not reclaim_stale:
                    raise ValueError("Run lease is held or has not been explicitly reconciled")
            atomic_write(self.root, ".agent/run.lock", json.dumps({"run_id": self.run_id, "owner": self.owner}).encode())
            self._held = True

    def release(self) -> None:
        with file_guard(self.root, ".agent/lease.guard"):
            path = confined_path(self.root, ".agent/run.lock")
            if not self._held or not path.exists():
                raise ValueError("Cannot release an unowned lease")
            prior = _object(json.loads(path.read_bytes()))
            if prior.get("run_id") != self.run_id or prior.get("owner") != self.owner:
                raise ValueError("Lease ownership changed")
            path.unlink()
            self._held = False

    def assert_held(self) -> None:
        with file_guard(self.root, ".agent/lease.guard"):
            path = confined_path(self.root, ".agent/run.lock")
            if not self._held or not path.exists():
                raise ValueError("Run transition requires a held lease")
            record = _object(json.loads(path.read_bytes()))
            if record.get("run_id") != self.run_id or record.get("owner") != self.owner:
                raise ValueError("Run lease identity changed")


class RunLifecycle:
    def __init__(self, root: Path, run_id: str, *, contract_version: int, contract_sha256: str) -> None:
        self.root, self.run_id, self.prefix = root, run_id, run_prefix(run_id)
        self.contract_version, self.contract_sha256 = contract_version, contract_sha256

    def finish(self, outcome: str, *, candidate_revision: str | None, reason: str,
               evidence_refs: tuple[str, ...] = ()) -> dict[str, object]:
        if outcome not in ("operational", "cancelled", "rework", "abandon", "awaiting_human_review"):
            raise ValueError("Accepted pass requires the later human/provenance gate")
        for ref in evidence_refs:
            confined_path(self.root, ref)
        result: dict[str, object] = {"format_version": 1, "run_id": self.run_id,
            "contract_version": self.contract_version, "contract_sha256": self.contract_sha256,
            "outcome": outcome, "candidate_revision": candidate_revision, "reason": reason,
            "evidence_refs": list(evidence_refs)}
        atomic_write(self.root, self.prefix + "/result.json", json.dumps(result, sort_keys=True).encode())
        return result

    def cancel(self, *, candidate_revision: str | None, active_owner: str | None,
               stop_owned: Callable[[str], None]) -> dict[str, object]:
        atomic_write(self.root, self.prefix + "/cancel.json", json.dumps({"requested": True, "owner": active_owner}).encode())
        if active_owner is not None:
            stop_owned(active_owner)
        return self.finish("cancelled", candidate_revision=candidate_revision, reason="Explicit cancellation reconciled")
