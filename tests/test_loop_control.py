"""Frozen deterministic retry policy and owned rollback acceptance."""

from dataclasses import replace

import pytest

from test_contracts import bundle, load
from unity_coder.core.loop_control import Observation, RetryPolicy, classify, capture_owned, restore_owned


def obs(*failures, gate="tests"):
    return Observation(gate, tuple(failures))


@pytest.mark.parametrize("previous,current,expected", [
    (None, obs("A"), "RED"), (obs("A", "B"), obs("A"), "PROGRESSING"),
    (obs("A"), obs("A"), "STALLED"), (obs("A"), obs("B"), "REGRESSED"),
    (obs("C", gate="compile"), obs("A"), "PROGRESSING"),
    (obs("A"), obs("C", gate="compile"), "REGRESSED"),
    (obs("A", "B"), replace(obs("B", "A"), message="cosmetic change"), "STALLED"),
])
def test_gate_specific_trends(previous, current, expected):
    assert classify(previous, current) == expected


@pytest.mark.parametrize("field,value", [("selection", ("Other",)), ("environment", "other"),
                                         ("contract_sha256", "other"), ("baseline_sha256", "other")])
def test_incomparable_evidence_does_not_invent_progress(field, value):
    assert classify(obs("A", "B"), replace(obs("A"), **{field: value})) is None


def test_stalled_overrides_implementation_judge_immediately():
    policy = RetryPolicy(max_attempts=3)
    assert policy.evaluate("U1", obs("A"), judge_class="implementation").kind == "retry"
    result = policy.evaluate("U1", obs("A"), judge_class="implementation")
    assert result.kind == "escalate" and result.defect_class == "contract"


def test_first_regression_restores_and_second_escalates_across_stages():
    policy = RetryPolicy(max_attempts=5)
    policy.evaluate("U1", obs("A"), judge_class="implementation")
    first = policy.evaluate("U1", obs("A", "B"), judge_class="implementation", stage="green")
    assert first.kind == "restore_retry"
    second = policy.evaluate("U1", obs("A", "B", "C"), judge_class="implementation", stage="refactor")
    assert second.kind == "restore_escalate" and second.defect_class == "contract"
    assert policy.state("U1").regressions == 2


def test_failed_exhaustion_overrides_progress_and_judge():
    policy = RetryPolicy(max_attempts=3)
    for failures in [("A", "B", "C"), ("A", "B"), ("A",)]:
        result = policy.evaluate("U1", obs(*failures), judge_class="implementation")
    assert result.kind == "escalate" and result.defect_class == "contract"
    assert policy.state("U1").failed_attempts == 3


def test_successful_last_permitted_candidate_passes():
    policy = RetryPolicy(max_attempts=3)
    policy.evaluate("U1", obs("A", "B"), judge_class="implementation")
    policy.evaluate("U1", obs("A"), judge_class="implementation")
    result = policy.evaluate("U1", None, passed=True)
    assert result.kind == "pass"
    assert policy.state("U1").failed_attempts == 2


def test_expected_red_never_spends_repair_attempt():
    policy = RetryPolicy(max_attempts=3)
    policy.evaluate("U1", obs("A"), expected_red=True)
    assert policy.state("U1").failed_attempts == 0
    assert policy.state("U1").history == ()


def test_incomparable_failure_requires_explicit_review():
    policy = RetryPolicy(max_attempts=3)
    policy.evaluate("U1", obs("A", "B"), judge_class="implementation")
    result = policy.evaluate("U1", replace(obs("A"), environment="changed"), judge_class="implementation")
    assert result.kind == "review" and result.trend is None


def test_contract_judge_returns_to_architect_without_retry():
    result = RetryPolicy().evaluate("U1", obs("A"), judge_class="contract")
    assert result.kind == "escalate" and result.defect_class == "contract"


def test_owned_restore_retains_peer_and_invalidates_shared_evidence(bundle):
    contract, root = load(bundle), bundle[1]
    own = root / "Runtime/Script/Queue/DinerState.cs"
    peer = root / "Runtime/Script/Queue/QueueSystem.cs"
    own.parent.mkdir(parents=True)
    own.write_bytes(b"safe")
    peer.write_bytes(b"peer before")
    snapshot = capture_owned(root, contract, "U1-state", "before")
    own.write_bytes(b"regression")
    peer.write_bytes(b"peer after")
    kept = restore_owned(root, contract, snapshot, {"U1-state": "old", "U2-system": "dependent"})
    assert own.read_bytes() == b"safe" and peer.read_bytes() == b"peer after"
    assert kept == {}
