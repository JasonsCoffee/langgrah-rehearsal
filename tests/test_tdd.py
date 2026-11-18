"""Frozen test-first phase barrier and Red/Green/Refactor acceptance."""

from dataclasses import replace

import pytest

from test_contracts import bundle, load, Rules
from unity_coder.core.evidence import TestResult as Result
from unity_coder.core.tdd import BehaviorEvidence, TDDCoordinator


@pytest.fixture
def coordinator(bundle):
    contract = load(bundle)
    root = bundle[1]
    for unit in contract.units:
        for file in unit.owns:
            path = root / file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"baseline")
    (root / "test-config.json").write_bytes(b"{}")
    return TDDCoordinator(contract, root, Rules(), test_config_paths=("test-config.json",), max_preparation_attempts=2)


def evidence(c, unit_id, *, snapshot="base", failed=True, kind="assertion"):
    tests = next(u.acceptance for u in c.contract.units if u.id == unit_id)
    return BehaviorEvidence(snapshot, tests, Result(tests, tests, () if failed else tests, tests if failed else ()), kind)


def prepare(c):
    c.approve_tests("U0-tests", "independent-coverage-review")
    c.record_baseline("U1-state", evidence(c, "U1-state"))
    c.record_baseline("U2-system", evidence(c, "U2-system"))
    c.freeze()


def test_global_barrier_blocks_implementation(coordinator):
    with pytest.raises(ValueError): coordinator.begin("U1-state")
    with pytest.raises(ValueError): coordinator.freeze()


def test_all_authors_and_all_baselines_required(coordinator):
    c = coordinator
    c.approve_tests("U0-tests", "review")
    c.record_baseline("U1-state", evidence(c, "U1-state"))
    with pytest.raises(ValueError): c.freeze()
    c.record_baseline("U2-system", evidence(c, "U2-system"))
    c.freeze()
    assert c.frozen
    assert c.state("U1-state").stage == "red_evidenced"


@pytest.mark.parametrize("kind", ["structural", "operational", "invalid_test"])
def test_nonbehavioral_failures_are_not_red(coordinator, kind):
    with pytest.raises(ValueError):
        coordinator.record_baseline("U1-state", evidence(coordinator, "U1-state", kind=kind))


@pytest.mark.parametrize("outcome", ["zero", "missing", "skip", "inconclusive"])
def test_invalid_test_execution_cannot_establish_red(coordinator, outcome):
    ev = evidence(coordinator, "U1-state")
    if outcome == "zero": result = Result((), (), (), ())
    elif outcome == "missing": result = replace(ev.result, executed=ev.result.executed[:-1])
    elif outcome == "skip": result = replace(ev.result, skipped=(ev.requested[0],))
    else: result = replace(ev.result, inconclusive=(ev.requested[0],))
    with pytest.raises(ValueError): coordinator.record_baseline("U1-state", replace(ev, result=result))


def test_already_passing_requires_recorded_coverage_review(coordinator):
    ev = evidence(coordinator, "U1-state", failed=False)
    with pytest.raises(ValueError): coordinator.record_baseline("U1-state", ev)
    coordinator.record_baseline("U1-state", ev, coverage_review="independent coverage confirms requirement")
    assert coordinator.state("U1-state").already_satisfied


def test_red_does_not_consume_implementation_attempts_or_erase_usage(coordinator):
    coordinator.record_model_usage("test-call", 100, 20)
    prepare(coordinator)
    assert coordinator.state("U1-state").failed_attempts == 0
    assert coordinator.model_input_tokens == 100
    assert coordinator.model_output_tokens == 20


@pytest.mark.parametrize("path", ["Tests/Runtime/Script/QueueReorderTests.cs", "test-config.json"])
def test_frozen_test_and_config_patch_rejected(coordinator, path):
    prepare(coordinator)
    with pytest.raises(ValueError): coordinator.validate_patch("U1-state", {path: b"weakened"})


def test_out_of_band_test_edit_blocks_dispatch(coordinator):
    prepare(coordinator)
    (coordinator.root / "test-config.json").write_bytes(b"changed")
    with pytest.raises(ValueError): coordinator.begin("U1-state")


def test_test_author_cannot_rewrite_after_freeze(coordinator):
    prepare(coordinator)
    with pytest.raises(ValueError):
        coordinator.validate_patch("U0-tests", {"Tests/Runtime/Script/QueueReorderTests.cs": b"changed"})


def test_refactor_requires_verified_green_and_a_reason(coordinator):
    prepare(coordinator)
    with pytest.raises(ValueError): coordinator.begin_refactor("U1-state")
    coordinator.begin("U1-state")
    coordinator.record_green("U1-state", evidence(coordinator, "U1-state", snapshot="green", failed=False))
    with pytest.raises(ValueError): coordinator.finish_refactor("U1-state", reason="")
    coordinator.finish_refactor("U1-state", reason="No safe simplification needed")
    assert coordinator.state("U1-state").stage == "complete"


def test_failed_refactor_requests_green_restore_and_retains_attempts(coordinator):
    prepare(coordinator)
    coordinator.begin("U1-state")
    coordinator.record_green("U1-state", evidence(coordinator, "U1-state", snapshot="green", failed=False))
    coordinator.begin_refactor("U1-state")
    restore = coordinator.finish_refactor("U1-state", evidence(coordinator, "U1-state", snapshot="bad-refactor"))
    assert restore == "green"
    assert coordinator.state("U1-state").stage == "green_verified"
    assert coordinator.state("U1-state").failed_attempts == 1


def test_refactor_pass_records_new_snapshot(coordinator):
    prepare(coordinator)
    coordinator.begin("U1-state")
    coordinator.record_green("U1-state", evidence(coordinator, "U1-state", snapshot="green", failed=False))
    coordinator.begin_refactor("U1-state")
    coordinator.finish_refactor("U1-state", evidence(coordinator, "U1-state", snapshot="refactored", failed=False))
    assert coordinator.state("U1-state").stage == "complete"
    assert coordinator.state("U1-state").accepted_snapshot == "refactored"


def test_missing_peer_is_pending_not_a_failed_attempt(coordinator):
    prepare(coordinator)
    coordinator.begin("U1-state")
    coordinator.pending_shared("U1-state")
    assert coordinator.state("U1-state").stage == "pending_shared_verification"
    assert coordinator.state("U1-state").failed_attempts == 0
    with pytest.raises(ValueError):
        coordinator.record_group_green(("U1-state",), evidence(coordinator, "U1-state", failed=False))


def test_preparation_has_its_own_bound(coordinator):
    coordinator.record_preparation_failure("U0-tests")
    with pytest.raises(ValueError): coordinator.record_preparation_failure("U0-tests")
    with pytest.raises(ValueError): coordinator.approve_tests("U0-tests", "late review")


def test_model_call_accounting_is_idempotent(coordinator):
    coordinator.record_model_usage("same-call", 100, 20)
    coordinator.record_model_usage("same-call", 100, 20)
    assert coordinator.model_input_tokens == 100
    with pytest.raises(ValueError): coordinator.record_model_usage("same-call", 101, 20)
