"""Frozen exact-candidate human resume through the production graph."""

import pytest

from test_local_executor import local, run
from test_workspaces import workspace, git
from test_contracts import bundle
from unity_coder.core.local_executor import _verification


def test_accepted_review_finalizes_only_metadata_and_does_not_recode(local):
    executor,services,workers,_,_,review = local
    run(executor)
    evidence = _verification(services.state["verification"])
    calls = list(workers.calls)
    review.decide("credential",evidence.request,"accept",findings=())
    executor.resume_review()
    assert run(executor)["outcome"] == "pass"
    assert workers.calls == calls
    assert git(services.integration.path,"rev-parse","HEAD^") == evidence.request.candidate_revision


def test_pending_review_cannot_resume_or_self_approve(local):
    executor,_,workers,_,_,_ = local
    run(executor)
    calls = list(workers.calls)
    with pytest.raises(ValueError):
        executor.resume_review()
    assert workers.calls == calls


def test_implementation_review_reverifies_under_same_contract_and_budget(local):
    executor,services,workers,verified,_,review = local
    run(executor)
    evidence = _verification(services.state["verification"])
    executor.budget.reserve("prior-usage","U1-state",25,10)
    review.decide("credential",evidence.request,"implementation",findings=("Owned behavior needs repair",))
    executor.resume_review()
    assert run(executor)["outcome"] == "awaiting_human_review"
    assert executor.budget.totals() == (25,10)
    assert all(r.contract_version == 1 for r in verified)
    assert verified[-1].request_id != evidence.request.request_id
    assert review.state()["decision"] == "pending"
    assert [s for _,s in workers.calls].count("green") == 4


def test_contract_review_emits_dossier_and_ends_without_coding(local):
    executor,services,workers,_,_,review = local
    run(executor)
    evidence = _verification(services.state["verification"])
    calls = list(workers.calls)
    review.decide("credential",evidence.request,"contract",findings=("Layout contract must change",))
    executor.resume_review()
    assert run(executor)["outcome"] == "rework"
    assert workers.calls == calls
    assert (executor.root / executor.prefix / "dossier-v1.json").exists()
