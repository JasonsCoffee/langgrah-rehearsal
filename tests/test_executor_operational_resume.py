"""Frozen explicit operational recovery without resetting run accounting."""

import pytest
from test_executor_graph import executor, invoke
from test_contracts import bundle
from test_workspaces import workspace, git
from unity_coder.core.executor import StepResult
from unity_coder.core.lifecycle import RunLifecycle
from unity_coder.core.workspaces import WorkspaceManager


def test_operational_resume_requires_reconciliation_and_keeps_prior_stages(executor):
    worker,services,budget=executor
    original=services.step
    failed=[]
    def step(stage,operation):
        if stage=="red" and not failed:
            failed.append(True)
            services.calls.append((stage,operation))
            receipt=RunLifecycle(worker.root,worker.run_id,contract_version=1,contract_sha256=worker.contract.sha256).finish(
                "operational",candidate_revision="baseline",reason="verifier unavailable")
            return StepResult("ended",{},receipt)
        return original(stage,operation)
    services.step=step
    assert invoke(worker)["outcome"]=="operational"
    budget.reserve("old-paid","U1-state",25,10)
    with pytest.raises(ValueError):
        worker.resume_operational(reconcile=lambda:False)
    worker.resume_operational(reconcile=lambda:True)
    assert invoke(worker)["outcome"]=="awaiting_human_review"
    assert budget.totals()==(25,10)
    assert [s for s,_ in services.calls].count("prepare")==1
    assert [s for s,_ in services.calls].count("red")==2


def test_reopen_existing_integration_checks_branch_and_repository(workspace):
    manager,repo,base,contract=workspace
    first=manager.create_integration(1,base)
    restarted=WorkspaceManager(repo,manager.workspace_root,contract,manager.rules,run_id=manager.run_id,imported_roots=(repo.parent,))
    reopened=restarted.reopen_integration(1,base)
    assert reopened==first
    restarted._assert_handle(reopened,"integration")
    git(first.path,"switch","--detach",base)
    with pytest.raises(ValueError):
        restarted.reopen_integration(1,base)
