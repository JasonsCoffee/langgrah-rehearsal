"""Frozen durable observability; status is not a completion signal."""

import json
import os
import time
from threading import Thread

import pytest

from unity_coder.core.progress import ProgressStore


def read_status(path, *, windows=os.name == "nt", clock=time.monotonic, pause=time.sleep):
    """Approved v2 reader: retry only access errors, never malformed JSON."""
    deadline = clock() + 2.0
    while True:
        try:
            return json.loads(path.read_bytes())
        except PermissionError:
            if not windows or clock() >= deadline:
                raise
            pause(0.001)


def test_reader_retries_transient_windows_access_error():
    class Source:
        calls = 0
        def read_bytes(self):
            self.calls += 1
            if self.calls < 3:
                raise PermissionError("sharing violation")
            return b'{"sequence": 1}'
    source = Source()
    assert read_status(source, windows=True, clock=lambda: 0, pause=lambda _: None) == {"sequence": 1}
    assert source.calls == 3


def test_reader_rejects_partial_json_without_retry():
    class Source:
        calls = 0
        def read_bytes(self):
            self.calls += 1
            return b'{"sequence":'
    source = Source()
    with pytest.raises(json.JSONDecodeError):
        read_status(source, windows=True)
    assert source.calls == 1


def test_reader_rejects_persistent_access_failure():
    class Source:
        calls = 0
        def read_bytes(self):
            self.calls += 1
            raise PermissionError("persistent denial")
    source = Source()
    ticks = iter((0.0, 1.0, 2.0))
    with pytest.raises(PermissionError):
        read_status(source, windows=True, clock=lambda: next(ticks), pause=lambda _: None)
    assert source.calls == 2


def test_reader_does_not_retry_other_io_errors():
    class Source:
        def read_bytes(self):
            raise FileNotFoundError("missing")
    with pytest.raises(FileNotFoundError):
        read_status(Source(), windows=True)


def test_progress_sequences_and_unit_stages_survive_restart(tmp_path):
    store = ProgressStore(tmp_path, "run1", contract_version=1, contract_sha256="hash")
    first = store.publish("coding", units={"U1": "green_coding", "U2": "pending_shared_verification"}, active_verification="candidate1")
    second = ProgressStore(tmp_path, "run1", contract_version=1, contract_sha256="hash").heartbeat()
    assert first["sequence"] == 1 and second["sequence"] == 2
    assert second["units"] == first["units"]
    assert second["active_verification"] == "candidate1" and second["heartbeat_utc"]
    assert second["stage"] == "coding" and "outcome" not in second


def test_status_is_always_complete_json_during_updates(tmp_path):
    store = ProgressStore(tmp_path, "run1", contract_version=1, contract_sha256="hash")
    store.publish("coding", units={})
    errors = []
    def writer():
        try:
            for _ in range(10): store.heartbeat()
        except Exception as exc: errors.append(exc)
    thread = Thread(target=writer)
    thread.start()
    while thread.is_alive():
        try: read_status(tmp_path / ".agent/runs/run1/status.json")
        except Exception as exc: errors.append(exc)
    thread.join()
    assert errors == []
    assert store.status()["sequence"] == 11


def test_journal_ahead_of_snapshot_reconciles_on_reconnect(tmp_path):
    store = ProgressStore(tmp_path, "run1", contract_version=1, contract_sha256="hash")
    first = store.publish("coding", units={})
    store.heartbeat()
    (tmp_path / ".agent/runs/run1/status.json").write_text(json.dumps(first))
    recovered = ProgressStore(tmp_path, "run1", contract_version=1, contract_sha256="hash").status()
    assert recovered["sequence"] == 2
