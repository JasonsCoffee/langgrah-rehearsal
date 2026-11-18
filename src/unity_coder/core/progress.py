"""Atomic snapshots backed by an ordered durable observability log."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from .contracts import _object, _text
from .journal import run_prefix
from .ownership import confined_path
from .storage import atomic_write, file_guard


class ProgressStore:
    def __init__(self, root: Path, run_id: str, *, contract_version: int, contract_sha256: str) -> None:
        self.root, self.run_id, self.prefix = root, run_id, run_prefix(run_id)
        self.contract_version, self.contract_sha256 = contract_version, contract_sha256

    def _records(self) -> list[dict[str, object]]:
        path = confined_path(self.root, self.prefix + "/progress.jsonl")
        records = [_object(json.loads(line)) for line in path.read_bytes().splitlines()] if path.exists() else []
        for sequence, record in enumerate(records, 1):
            if record.get("sequence") != sequence or record.get("run_id") != self.run_id:
                raise ValueError("Progress log sequence or identity is corrupt")
        return records

    def _current(self) -> dict[str, object]:
        records = self._records()
        if not records:
            return {}
        current = records[-1]
        if current.get("contract_version") != self.contract_version or current.get("contract_sha256") != self.contract_sha256:
            raise ValueError("Progress belongs to a different contract invocation")
        atomic_write(self.root, self.prefix + "/status.json", json.dumps(current, sort_keys=True).encode())
        return current

    def status(self) -> dict[str, object]:
        with file_guard(self.root, self.prefix + "/progress.guard"):
            return self._current()

    def _publish(self, stage: str, units: Mapping[str, str], active_verification: str | None,
                  attempts: Mapping[str, int], budget: Mapping[str, int], *,
                  previous: tuple[int, str] | None = None) -> dict[str, object]:
        records = self._records()
        if records and (records[-1].get("contract_version") != self.contract_version or records[-1].get("contract_sha256") != self.contract_sha256):
            if previous != (records[-1].get("contract_version"), records[-1].get("contract_sha256")):
                raise ValueError("Explicit cycle transition required before publishing another contract")
        record: dict[str, object] = {"format_version": 1, "run_id": self.run_id,
            "contract_version": self.contract_version, "contract_sha256": self.contract_sha256,
            "sequence": len(records) + 1, "heartbeat_utc": datetime.now(timezone.utc).isoformat(),
            "stage": stage, "units": dict(units), "attempts": dict(attempts), "budget": dict(budget),
            "active_verification": active_verification}
        records.append(record)
        # Replace the whole log atomically: interruption cannot leave a torn tail.
        content = b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in records)
        atomic_write(self.root, self.prefix + "/progress.jsonl", content)
        atomic_write(self.root, self.prefix + "/status.json", json.dumps(record, sort_keys=True).encode())
        return record

    def transition(self, previous_version: int, previous_sha256: str) -> dict[str, object]:
        """Called by the leased cycle transaction, preserving global sequence."""
        if self.contract_version != previous_version + 1:
            raise ValueError("Progress transition must be consecutive")
        with file_guard(self.root, self.prefix + "/progress.guard"):
            records = self._records()
            if records and (records[-1].get("contract_version"), records[-1].get("contract_sha256")) == (
                self.contract_version, self.contract_sha256):
                return self._current()
            if records and (records[-1].get("contract_version"), records[-1].get("contract_sha256")) != (
                previous_version, previous_sha256):
                raise ValueError("Progress transition predecessor mismatch")
            return self._publish("cycle_ready", {}, None, {}, {}, previous=(previous_version, previous_sha256))

    def publish(self, stage: str, *, units: Mapping[str, str], active_verification: str | None = None,
                attempts: Mapping[str, int] | None = None, budget: Mapping[str, int] | None = None) -> dict[str, object]:
        with file_guard(self.root, self.prefix + "/progress.guard"):
            return self._publish(stage, units, active_verification, attempts or {}, budget or {})

    def heartbeat(self) -> dict[str, object]:
        with file_guard(self.root, self.prefix + "/progress.guard"):
            current = self._current()
            if not current:
                raise ValueError("No active status to heartbeat")
            units = {k: _text(v) for k, v in _object(current["units"]).items()}
            counters: list[dict[str, int]] = []
            for name in ("attempts", "budget"):
                parsed: dict[str, int] = {}
                for key, value in _object(current[name]).items():
                    if type(value) is not int or value < 0:
                        raise ValueError("Invalid persisted resource counter")
                    parsed[key] = value
                counters.append(parsed)
            active = current["active_verification"]
            return self._publish(_text(current["stage"]), units,
                                 None if active is None else _text(active), counters[0], counters[1])
