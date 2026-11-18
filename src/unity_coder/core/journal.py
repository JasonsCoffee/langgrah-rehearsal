"""Persist operation intent and reconcile external effects before replay."""

import json
from pathlib import Path
import re
from typing import Callable

from .contracts import _object, _text
from .ownership import confined_path
from .storage import atomic_write, file_guard


def run_prefix(run_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id):
        raise ValueError("Unsafe run ID")
    return f".agent/runs/{run_id}"


class OperationJournal:
    def __init__(self, root: Path, run_id: str) -> None:
        self.root, self.prefix = root, run_prefix(run_id)

    def _path(self, operation_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", operation_id):
            raise ValueError("Unsafe operation ID")
        return f"{self.prefix}/operations/{operation_id}.json"

    def _read(self, operation_id: str) -> dict[str, object]:
        return _object(json.loads(confined_path(self.root, self._path(operation_id)).read_bytes()))

    def _write(self, operation_id: str, record: dict[str, object]) -> None:
        atomic_write(self.root, self._path(operation_id), json.dumps(record, sort_keys=True).encode())

    def begin(self, operation_id: str, *, kind: str, before: str, after: str,
              owner: str, request_id: str = "") -> dict[str, object]:
        if kind not in ("apply", "verify") or not before or not after or not owner or (kind == "verify" and not request_id):
            raise ValueError("Incomplete operation intent")
        record: dict[str, object] = {"operation_id": operation_id, "kind": kind, "before": before,
                                     "after": after, "owner": owner, "request_id": request_id, "state": "pending"}
        with file_guard(self.root, self.prefix + "/operations.guard"):
            if confined_path(self.root, self._path(operation_id)).exists():
                prior = self._read(operation_id)
                if any(prior.get(k) != v for k, v in record.items() if k != "state"):
                    raise ValueError("Operation identity changed")
                return prior
            self._write(operation_id, record)
        return record

    def reconcile(self, operation_id: str, *, actual_revision: str,
                  owner_alive: Callable[[str], bool]) -> str:
        with file_guard(self.root, self.prefix + "/operations.guard"):
            record = self._read(operation_id)
            if actual_revision not in (record["before"], record["after"]):
                raise ValueError("External state conflicts with recorded operation")
            if record["state"] == "complete":
                if actual_revision != record["after"]:
                    raise ValueError("Completed operation no longer matches current state")
                return "complete"
            if owner_alive(_text(record["owner"])):
                return "wait"
            if record["kind"] == "apply" and actual_revision == record["after"]:
                record["state"] = "complete"
                self._write(operation_id, record)
                return "complete"
            return "retry"

    def complete_verification(self, operation_id: str, *, request_id: str,
                              candidate_revision: str, evidence_ref: str) -> None:
        with file_guard(self.root, self.prefix + "/operations.guard"):
            record = self._read(operation_id)
            if record["kind"] != "verify" or record["request_id"] != request_id or record["after"] != candidate_revision:
                raise ValueError("Stale verification completion")
            evidence = _object(json.loads(confined_path(self.root, evidence_ref).read_bytes()))
            if evidence.get("request_id") != request_id or evidence.get("candidate_revision") != candidate_revision:
                raise ValueError("Persisted verification evidence does not match request")
            record.update(state="complete", evidence_ref=evidence_ref)
            self._write(operation_id, record)
