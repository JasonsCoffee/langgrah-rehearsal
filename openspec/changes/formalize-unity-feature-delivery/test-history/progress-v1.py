"""Frozen durable observability; status is not a completion signal."""

import json
from threading import Thread

from unity_coder.core.progress import ProgressStore


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
        try: json.loads((tmp_path / ".agent/runs/run1/status.json").read_bytes())
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
