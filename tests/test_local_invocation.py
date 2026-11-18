"""Frozen Architect-to-production graph invocation wiring."""

from test_local_executor import local
from test_workspaces import workspace
from test_contracts import bundle
from test_architect_boundary import planning
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.core.local_executor import _verification
from unity_coder.cli import invoke_local


def test_local_boundary_invokes_graph_and_returns_review_then_accepted_tasks(local, planning):
    executor, services, workers, _, _, review = local
    payload, sources, contract, root = planning
    boundary = ArchitectBoundary(root,executor.root,executor.run_id,executor.contract,
                                  discover_context(root,payload,sources=sources))
    report = invoke_local(boundary,executor)
    assert report["result"]["outcome"] == "awaiting_human_review"
    assert report["eligible_tasks"] == []
    before = list(workers.calls)
    assert invoke_local(boundary,executor)["next_action"] == "wait"
    assert workers.calls == before
    evidence = _verification(services.state["verification"])
    review.decide("credential",evidence.request,"accept",findings=())
    report = invoke_local(boundary,executor)
    assert report["result"]["outcome"] == "pass"
    assert report["eligible_tasks"] == ["queue-reorder:1.1"]


def test_local_boundary_contract_review_persists_rework_dossier(local, planning):
    executor, services, _, _, _, review = local
    payload, sources, contract, root = planning
    boundary = ArchitectBoundary(root,executor.root,executor.run_id,executor.contract,
                                  discover_context(root,payload,sources=sources))
    invoke_local(boundary,executor)
    review.decide("credential",_verification(services.state["verification"]).request,"contract",findings=("Revise layout",))
    report = invoke_local(boundary,executor)
    assert report["result"]["outcome"] == "rework"
    assert (executor.root / executor.prefix / "dossier-v1.json").exists()
