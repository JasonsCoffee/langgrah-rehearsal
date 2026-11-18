"""Frozen last-cycle governor wiring after authenticated contract rework."""

from test_local_executor import local, run
from test_workspaces import workspace, git
from test_contracts import bundle
from unity_coder.core.local_executor import _verification
from unity_coder.core.budget import BudgetLedger


def test_last_permitted_cycle_rework_abandons_and_retains_candidate(local):
    executor,services,_,_,repo,review=local
    budget=BudgetLedger(executor.root,executor.run_id,input_limit=100000,output_limit=20000,max_cycles=1,max_added_units=2)
    executor.budget=services.budget=budget
    run(executor)
    request=_verification(services.state["verification"]).request
    review.decide("credential",request,"contract",findings=("Missing layout contract",))
    executor.resume_review()
    assert run(executor)["outcome"]=="abandon"
    assert git(repo,"rev-parse","refs/heads/agent/run1/cycle-1")==request.candidate_revision
    assert git(services.integration.path,"rev-parse","HEAD")==git(repo,"rev-parse","HEAD")
