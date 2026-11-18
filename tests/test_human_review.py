"""Frozen review transition acceptance using a trusted fake human boundary."""

from dataclasses import replace
import json

import pytest

from unity_coder.core.review import ReviewGate
from unity_coder.core.lifecycle import RunLifecycle
from unity_coder.core.verification import VerificationRequest, VerificationResult
from unity_coder.core.evidence import TestResult


@pytest.fixture
def review(tmp_path):
    lifecycle = RunLifecycle(tmp_path, "run1", contract_version=1, contract_sha256="contract")
    def gate():
        return ReviewGate(lifecycle, authenticate_human=lambda token: "reviewer1" if token == "human-token" else None)
    request = VerificationRequest("req1", "run1", 1, "contract", "candidate1", "baseline", "profile", "environment", ("Test",), True)
    evidence = VerificationResult(request, "tests", "passed", test_result=TestResult(("Test",), ("Test",), ("Test",), ()),
                                  full_suite_verified=True, behavioral=True)
    files = {"code.txt": b"code", "asset.bin": b"art", "AGENTS.md": b"starting notes"}
    return gate, evidence, files, tmp_path


def test_waiting_does_not_accept_or_flush(review):
    factory, evidence, files, root = review
    result = factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    assert result["outcome"] == "awaiting_human_review"
    assert not (root / "AGENTS.md").exists()
    assert factory().state()["candidate_revision"] == "candidate1"


@pytest.mark.parametrize("changes", [{"status": "operational"}, {"status": "failed"},
    {"gate": "compile"}, {"full_suite_verified": False}, {"behavioral": False}])
def test_nonrunnable_or_incomplete_evidence_cannot_request_review(review, changes):
    factory, evidence, files, _ = review
    with pytest.raises(ValueError):
        factory().offer(replace(evidence, **changes), files, evidence_refs=("evidence/tests.json",))


def test_agent_cannot_self_approve(review):
    factory, evidence, files, _ = review
    factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    with pytest.raises(ValueError):
        factory().decide("agent-token", evidence.request, "accept", findings=())


@pytest.mark.parametrize("field", ["candidate_revision", "presentation_sha256", "contract_sha256", "environment_sha256"])
def test_stale_review_is_rejected(review, field):
    factory, evidence, files, _ = review
    factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    with pytest.raises(ValueError):
        factory().decide("human-token", replace(evidence.request, **{field: "changed"}), "accept", findings=())


@pytest.mark.parametrize("decision,action", [("implementation", "repair"), ("contract", "rework")])
def test_findings_route_without_changing_cycle(review, decision, action):
    factory, evidence, files, _ = review
    factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    result = factory().decide("human-token", evidence.request, decision, findings=("button behavior",))
    assert result["action"] == action and result["contract_version"] == 1
    assert result["reviewer"] == "reviewer1"
    assert factory().state()["decision"] == decision
    with pytest.raises(ValueError):
        factory().finalize(evidence.request, parent_revision="candidate1", completion_revision="done", files=files)


def test_completion_is_metadata_only_and_bound_to_approved_parent(review):
    factory, evidence, files, root = review
    factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    factory().decide("human-token", evidence.request, "accept", findings=())
    completed = dict(files, **{"AGENTS.md": b"starting notes\naccepted managed constraints"})
    result = factory().finalize(evidence.request, parent_revision="candidate1", completion_revision="completed", files=completed)
    assert result["outcome"] == "pass"
    assert result["approved_parent"] == "candidate1" and result["candidate_revision"] == "completed"
    assert json.loads((root / ".agent/runs/run1/result.json").read_bytes())["outcome"] == "pass"


@pytest.mark.parametrize("change", ["source", "asset", "parent"])
def test_finalization_cannot_change_reviewed_content_or_parent(review, change):
    factory, evidence, files, _ = review
    factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    factory().decide("human-token", evidence.request, "accept", findings=())
    mutated = dict(files)
    if change == "source": mutated["code.txt"] = b"changed"
    if change == "asset": mutated["asset.bin"] = b"changed"
    with pytest.raises(ValueError):
        factory().finalize(evidence.request, parent_revision="wrong" if change == "parent" else "candidate1",
                           completion_revision="completed", files=mutated)


def test_repair_candidate_requires_new_verification_and_approval(review):
    factory, evidence, files, _ = review
    factory().offer(evidence, files, evidence_refs=("evidence/tests.json",))
    factory().decide("human-token", evidence.request, "implementation", findings=("bug",))
    new = replace(evidence, request=replace(evidence.request, candidate_revision="candidate2", request_id="req2"))
    factory().offer(new, files, evidence_refs=("evidence/tests2.json",))
    with pytest.raises(ValueError):
        factory().finalize(new.request, parent_revision="candidate2", completion_revision="done", files=files)
    factory().decide("human-token", new.request, "accept", findings=())
    assert factory().finalize(new.request, parent_revision="candidate2", completion_revision="done", files=files)["outcome"] == "pass"
