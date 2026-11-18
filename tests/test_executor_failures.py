"""Frozen resource and operational failure routing in production services."""

from test_local_executor import local, run
from test_workspaces import workspace, git
from test_contracts import bundle
from unity_coder.core.budget import BudgetExhausted
from unity_coder.core.ai_models import ModelError


def test_reservation_exhaustion_abandons_without_coding_or_losing_branch(local):
    executor,services,workers,_,repo,_ = local
    def exhausted(*args):
        executor.budget.reserve("too-large","U1-state",100001,1)
    workers.code=exhausted
    assert run(executor)["outcome"] == "abandon"
    assert git(services.integration.path,"rev-parse","HEAD") == git(repo,"rev-parse","HEAD")
    assert git(repo,"rev-parse","refs/heads/agent/run1/cycle-1")
    assert (executor.root / executor.prefix / "dossier-v1.json").exists()


def test_model_transport_failure_is_operational_without_unit_attempt(local):
    executor,services,workers,_,_,_ = local
    def unavailable(*args):
        raise ModelError("Provider unavailable")
    workers.code=unavailable
    assert run(executor)["outcome"] == "operational"
    assert all(services.retry.state(u).failed_attempts==0 for u in services.tdd.units)
