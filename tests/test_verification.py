"""Frozen stop-first, provenance, and honest behavioral verification gates."""

from dataclasses import replace
from threading import Event, Thread

import pytest

from test_contracts import bundle, load
from fakes import FakeAdapter, FakeTransport
from unity_coder.core.evidence import CompileResult, TestResult as Result, Violation
from unity_coder.core.verification import VerificationLadder, VerificationRequest


@pytest.fixture
def verification(bundle):
    contract = load(bundle)
    tests = tuple(t.test_id for t in contract.test_links)
    request = VerificationRequest("request-1", "run-1", 1, contract.sha256, "candidate-1",
                                  contract.presentation_ref.sha256, contract.coding_profile_ref.sha256,
                                  contract.environment_ref.sha256, tests, True)
    patches = {"U1-state": {"Runtime/Script/Queue/DinerState.cs": b"source"}}
    return contract, request, patches, bundle[1]


def run(v, adapter=None, transport=None, **options):
    contract, request, patches, root = v
    worker = VerificationLadder(adapter or FakeAdapter(), transport or FakeTransport())
    return worker.verify(request, contract, root, patches, {"Runtime/Script/Queue/DinerState.cs": "source"}, **options)


def test_full_ladder_passes_in_order(verification):
    adapter, transport = FakeAdapter(), FakeTransport()
    result = run(verification, adapter, transport)
    assert result.status == "passed"
    assert result.full_suite_verified
    assert adapter.calls == ["parse", "interfaces"]
    assert transport.calls == ["compile", "tests"]


def test_ownership_failure_stops_every_later_gate(verification):
    verification[2]["U1-state"] = {"Runtime/Script/Queue/QueueSystem.cs": b"illegal"}
    adapter, transport = FakeAdapter(), FakeTransport()
    result = run(verification, adapter, transport)
    assert result.gate == "ownership" and result.status == "failed"
    assert result.related_units == ("U1-state",)
    assert adapter.calls == transport.calls == []


def test_frozen_generated_identity_is_rejected(verification):
    path = "Runtime/Script/Queue/DinerState.cs.meta"
    verification[2]["U1-state"] = {path: b"changed identity"}
    result = run(verification, frozen_paths=(path,))
    assert result.gate == "ownership" and result.status == "failed"


@pytest.mark.parametrize("gate", ["syntax", "interface", "compile"])
def test_structural_failure_stops_tests(verification, gate):
    violation = Violation(gate, "Runtime/Script/Queue/DinerState.cs", "State.M", "invalid")
    adapter = FakeAdapter(syntax=(violation,) if gate == "syntax" else (), interfaces=(violation,) if gate == "interface" else ())
    transport = FakeTransport(compilation=CompileResult(gate != "compile", (violation,) if gate == "compile" else ()))
    result = run(verification, adapter, transport)
    assert result.status == "failed"
    assert result.gate == ("compile" if gate == "compile" else "conformance")
    assert "tests" not in transport.calls
    assert result.related_units == ("U1-state",)


def test_shared_test_failure_retains_all_implementing_units(verification):
    tests = verification[1].test_selection
    transport = FakeTransport(result=Result(tests, tests, tests[1:], tests[:1]))
    result = run(verification, transport=transport)
    assert result.status == "failed" and result.gate == "tests"
    assert result.related_units == ("U1-state", "U2-system")
    assert result.failed_tests == tests[:1]


@pytest.mark.parametrize("problem", ["zero", "absent", "skip", "inconclusive", "contradictory"])
def test_incomplete_execution_cannot_pass(verification, problem):
    tests = verification[1].test_selection
    result = Result(tests, tests, tests, ())
    if problem == "zero": result = Result((), (), (), ())
    elif problem == "absent": result = Result(tests[:-1], tests[:-1], tests[:-1], ())
    elif problem == "skip": result = replace(result, skipped=tests[:1])
    elif problem == "inconclusive": result = replace(result, inconclusive=tests[:1])
    else: result = replace(result, failed=tests[:1])
    outcome = run(verification, transport=FakeTransport(result=result))
    assert outcome.status != "passed"
    assert not outcome.full_suite_verified
    assert any(v.code == "test_evidence" for v in outcome.violations)


def test_stale_results_are_operational_not_unit_failure(verification):
    result = run(verification, transport=FakeTransport(stale=True))
    assert result.status == "operational"
    assert result.related_units == ()


def test_missing_tooling_is_operational(verification):
    transport = FakeTransport(compilation=CompileResult(False, operational_error="tool unavailable"))
    result = run(verification, transport=transport)
    assert result.status == "operational" and result.related_units == ()
    assert transport.calls == ["compile"]


def test_focused_green_is_not_full_acceptance(verification):
    contract, request, patches, root = verification
    request = replace(request, test_selection=request.test_selection[:1], full_suite=False)
    result = run((contract, request, patches, root))
    assert result.status == "passed" and not result.full_suite_verified


def test_full_suite_request_cannot_omit_required_tests(verification):
    contract, request, patches, root = verification
    request = replace(request, test_selection=request.test_selection[:1])
    transport = FakeTransport()
    result = run((contract, request, patches, root), transport=transport)
    assert result.status != "passed" and transport.calls == []


def test_wrong_contract_identity_prevents_worker_calls(verification):
    contract, request, patches, root = verification
    transport = FakeTransport()
    result = run((contract, replace(request, contract_sha256="wrong"), patches, root), transport=transport)
    assert result.status == "operational" and transport.calls == []


def test_one_worker_blocks_until_results_and_serializes_requests(verification):
    entered, release, second_entered = Event(), Event(), Event()
    class BlockingTransport(FakeTransport):
        def compile(self, request):
            if request.request_id == "request-1":
                entered.set()
                assert release.wait(3)
            else:
                second_entered.set()
            return super().compile(request)
    c, request, patches, root = verification
    worker = VerificationLadder(FakeAdapter(), BlockingTransport())
    results = []
    def verify(req): results.append(worker.verify(req, c, root, patches, {}))
    first = Thread(target=verify, args=(request,))
    second = Thread(target=verify, args=(replace(request, request_id="request-2"),))
    first.start()
    try:
        assert entered.wait(2)
        second.start()
        assert not second_entered.wait(0.1)
        assert results == []
    finally:
        release.set()
        first.join(3)
        if second.ident is not None: second.join(3)
    assert len(results) == 2 and all(r.status == "passed" for r in results)
