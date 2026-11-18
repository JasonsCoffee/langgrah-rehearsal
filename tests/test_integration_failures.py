"""Frozen tests for explicit shared evidence and owned coordinated repairs."""

from dataclasses import replace

import pytest

from test_contracts import bundle
from test_verification import verification, run
from fakes import FakeTransport
from unity_coder.core.evidence import TestResult as Result
from unity_coder.core.integration import UnitDecision, RepairRounds, shared_failure, route_repairs, invalidate_dependents


@pytest.fixture
def failure(verification):
    contract, request, _, _ = verification
    tests = request.test_selection
    result = run(verification, transport=FakeTransport(result=Result(tests, tests, tests[1:], tests[:1])))
    return contract, shared_failure(contract, result, {"U1-state": "patch-1", "U2-system": "patch-2"})


def test_shared_evidence_distinguishes_authors_implementers_and_patches(failure):
    _, evidence = failure
    assert evidence.test_authors == ("U0-tests",)
    assert evidence.implementing_units == ("U1-state", "U2-system")
    assert evidence.candidate_revision == "candidate-1"
    assert evidence.patch_ids["U2-system"] == "patch-2"
    assert evidence.evidence_id


def test_coordinated_repairs_are_partitioned_by_owner(failure):
    contract, evidence = failure
    decisions = {
        "U1-state": UnitDecision("implementation", ("Runtime/Script/Queue/DinerState.cs",), "state logic"),
        "U2-system": UnitDecision("implementation", ("Runtime/Script/Queue/QueueSystem.cs",), "consumer logic"),
    }
    routing = route_repairs(contract, evidence, decisions)
    assert routing.can_dispatch
    assert set(routing.units) == {"U1-state", "U2-system"}
    assert all(u.defect_class == "implementation" and u.evidence_id == evidence.evidence_id for u in routing.units.values())


def test_mixed_verdicts_remain_per_unit(failure):
    contract, evidence = failure
    routing = route_repairs(contract, evidence, {
        "U1-state": UnitDecision("implementation", ("Runtime/Script/Queue/DinerState.cs",), "state repair"),
        "U2-system": UnitDecision("contract", (), "missing interface"),
    })
    assert routing.units["U1-state"].defect_class == "implementation"
    assert routing.units["U2-system"].defect_class == "contract"
    assert not routing.can_dispatch
    assert not hasattr(routing, "defect_class")


@pytest.mark.parametrize("mode", ["missing", "foreign_path", "frozen_path", "unknown_class"])
def test_ambiguous_or_unowned_repair_escalates(failure, mode):
    contract, evidence = failure
    decisions = {"U1-state": UnitDecision("implementation", ("Runtime/Script/Queue/DinerState.cs",), "repair"),
                 "U2-system": UnitDecision("implementation", ("Runtime/Script/Queue/QueueSystem.cs",), "repair")}
    frozen = ()
    if mode == "missing": decisions.pop("U2-system")
    elif mode == "foreign_path": decisions["U2-system"] = UnitDecision("implementation", ("Runtime/Script/Queue/DinerState.cs",), "steal")
    elif mode == "frozen_path": frozen = ("Runtime/Script/Queue/QueueSystem.cs",)
    else: decisions["U2-system"] = UnitDecision("unknown", (), "uncertain")
    routing = route_repairs(contract, evidence, decisions, frozen_paths=frozen)
    assert not routing.can_dispatch
    assert routing.units["U2-system"].defect_class == "contract"


def test_operational_evidence_does_not_make_shared_defect(verification):
    contract = verification[0]
    result = run(verification, transport=FakeTransport(stale=True))
    with pytest.raises(ValueError): shared_failure(contract, result, {})


def test_changed_unit_invalidates_dependents_but_preserves_unrelated(failure):
    contract, _ = failure
    independent = replace(contract.units[2], id="independent", acceptance=("Other.Test",), depends_on=(), owns=("Runtime/Script/Queue/Other.cs",))
    contract = replace(contract, units=contract.units + (independent,))
    evidence = {"U1-state": "proof1", "U2-system": "proof2", "independent": "proof3"}
    kept = invalidate_dependents(contract, ("U1-state",), evidence)
    assert kept == {"independent": "proof3"}
    assert evidence["U2-system"] == "proof2"


def test_one_failed_round_charges_each_participant_once():
    rounds = RepairRounds()
    rounds.charge_failure("round1", ("U1", "U2"))
    rounds.charge_failure("round1", ("U1", "U2"))
    assert rounds.failed_attempts == {"U1": 1, "U2": 1}
    with pytest.raises(ValueError): rounds.charge_failure("round1", ("U1",))
