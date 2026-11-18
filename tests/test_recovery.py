"""Frozen journal and lifecycle behavior across interruption and restart."""

import json

import pytest

from unity_coder.core.journal import OperationJournal
from unity_coder.core.lifecycle import RunLease, RunLifecycle


def test_crash_after_apply_reconciles_without_duplicate_patch(tmp_path):
    journal = OperationJournal(tmp_path, "run1")
    journal.begin("op1", kind="apply", before="base", after="candidate", owner="worker1")
    restarted = OperationJournal(tmp_path, "run1")
    assert restarted.reconcile("op1", actual_revision="candidate", owner_alive=lambda _: False) == "complete"
    assert restarted.reconcile("op1", actual_revision="candidate", owner_alive=lambda _: False) == "complete"


def test_unapplied_intent_can_retry_only_after_owner_is_gone(tmp_path):
    journal = OperationJournal(tmp_path, "run1")
    journal.begin("op1", kind="apply", before="base", after="candidate", owner="worker1")
    assert journal.reconcile("op1", actual_revision="base", owner_alive=lambda _: True) == "wait"
    assert journal.reconcile("op1", actual_revision="base", owner_alive=lambda _: False) == "retry"
    with pytest.raises(ValueError): journal.reconcile("op1", actual_revision="unexpected", owner_alive=lambda _: False)


def test_restart_cannot_launch_over_active_verifier(tmp_path):
    journal = OperationJournal(tmp_path, "run1")
    journal.begin("verify1", kind="verify", before="candidate", after="candidate", owner="editor1", request_id="request1")
    restarted = OperationJournal(tmp_path, "run1")
    assert restarted.reconcile("verify1", actual_revision="candidate", owner_alive=lambda _: True) == "wait"
    assert restarted.reconcile("verify1", actual_revision="candidate", owner_alive=lambda _: False) == "retry"


def test_stale_verifier_result_cannot_complete_operation(tmp_path):
    journal = OperationJournal(tmp_path, "run1")
    journal.begin("verify1", kind="verify", before="candidate", after="candidate", owner="editor1", request_id="request1")
    with pytest.raises(ValueError):
        journal.complete_verification("verify1", request_id="old", candidate_revision="candidate", evidence_ref="evidence/result.json")
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/result.json").write_text(json.dumps({"request_id": "request1", "candidate_revision": "candidate"}))
    journal.complete_verification("verify1", request_id="request1", candidate_revision="candidate", evidence_ref="evidence/result.json")
    assert journal.reconcile("verify1", actual_revision="candidate", owner_alive=lambda _: False) == "complete"


def test_operation_identity_is_immutable(tmp_path):
    journal = OperationJournal(tmp_path, "run1")
    journal.begin("op1", kind="apply", before="base", after="candidate", owner="worker1")
    with pytest.raises(ValueError): journal.begin("op1", kind="apply", before="base", after="other", owner="worker1")


def test_live_lease_cannot_be_stolen_or_released_by_another_owner(tmp_path):
    first = RunLease(tmp_path, "run1", "owner1")
    first.acquire(owner_alive=lambda _: True)
    other = RunLease(tmp_path, "run2", "owner2")
    with pytest.raises(ValueError): other.acquire(owner_alive=lambda _: True)
    with pytest.raises(ValueError): other.release()
    first.release()
    other.acquire(owner_alive=lambda _: True)
    other.release()


def test_stale_lease_requires_explicit_reclaim(tmp_path):
    RunLease(tmp_path, "run1", "owner1").acquire(owner_alive=lambda _: False)
    replacement = RunLease(tmp_path, "run2", "owner2")
    with pytest.raises(ValueError): replacement.acquire(owner_alive=lambda _: False)
    replacement.acquire(owner_alive=lambda _: False, reclaim_stale=True)
    replacement.release()


def test_cancellation_only_stops_owned_worker_and_keeps_candidate(tmp_path):
    lifecycle = RunLifecycle(tmp_path, "run1", contract_version=1, contract_sha256="hash")
    stopped = []
    result = lifecycle.cancel(candidate_revision="candidate", active_owner="owned-worker", stop_owned=stopped.append)
    assert stopped == ["owned-worker"]
    assert result["outcome"] == "cancelled" and result["candidate_revision"] == "candidate"
    assert "defect_class" not in result
    assert json.loads((tmp_path / ".agent/runs/run1/result.json").read_text())["outcome"] == "cancelled"


def test_operational_failure_does_not_manufacture_a_dossier(tmp_path):
    lifecycle = RunLifecycle(tmp_path, "run1", contract_version=1, contract_sha256="hash")
    result = lifecycle.finish("operational", candidate_revision="candidate", reason="worker unavailable")
    assert result["outcome"] == "operational"
    assert not list(tmp_path.rglob("dossier-*.json"))
