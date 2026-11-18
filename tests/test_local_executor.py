"""Frozen real-Git executor wiring with offline worker/verifier boundaries."""

from threading import Barrier

import pytest

from test_workspaces import workspace, git
from test_contracts import bundle
from unity_coder.core.local_executor import LocalExecutionServices, WorkerPatch
from unity_coder.core.executor import ProductionExecutor
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease, RunLifecycle
from unity_coder.core.review import ReviewGate
from unity_coder.core.verification import VerificationResult
from unity_coder.core.evidence import TestResult as Evidence
from unity_coder.graph import graph


class Workers:
    def __init__(self):
        self.calls = []
        self.barrier = Barrier(2)
        self.foreign = False

    def code(self, unit, stage, files, feedback, operation_id):
        self.calls.append((unit.id,stage))
        if stage == "refactor":
            return WorkerPatch({},"No change needed")
        self.barrier.wait(timeout=5)
        if self.foreign:
            return WorkerPatch({"shared.txt":b"wrong"},"invalid")
        return WorkerPatch({path:b"implemented" for path in unit.owns},"Implement criterion")

    def review_tests(self, unit, files, operation_id):
        return "Independent test validity and criterion coverage checked"

    def judge(self, unit, evidence, files, operation_id):
        return "implementation", "Repair the owned behavior"


@pytest.fixture
def local(workspace, tmp_path):
    manager, repo, base, contract = workspace
    integration = manager.create_integration(1,base)
    state = tmp_path / "state"
    budget = BudgetLedger(state,"run1",input_limit=100000,output_limit=20000,max_cycles=3,max_added_units=2)
    lease = RunLease(state,"run1","host")
    lease.acquire(owner_alive=lambda _:False)
    review = ReviewGate(RunLifecycle(state,"run1",contract_version=1,contract_sha256=contract.sha256),
                        authenticate_human=lambda value:"human" if value=="credential" else None)
    workers = Workers()
    verifications = []
    def verify(request,root,patches):
        assert git(root,"rev-parse","HEAD") == request.candidate_revision
        verifications.append(request)
        implemented = all((root / path).read_bytes()==b"implemented" for unit in contract.units
                          if unit.role=="impl" for path in unit.owns)
        tests = Evidence(discovered=request.test_selection,executed=request.test_selection,
                         passed=request.test_selection if implemented else (),
                         failed=() if implemented else request.test_selection)
        return VerificationResult(request,"tests","passed" if implemented else "failed",
                                  related_units=() if implemented else ("U1-state","U2-system"),
                                  failed_tests=tests.failed,test_result=tests,behavioral=True,
                                  full_suite_verified=implemented and request.full_suite)
    services = LocalExecutionServices(manager,integration,budget,workers,verify,review,
                                       preflight=lambda:None)
    executor = ProductionExecutor(state,"run1",contract,budget,lease,services)
    return executor,services,workers,verifications,repo,review


def run(executor):
    return graph.invoke({"run_id":executor.run_id,"contract_sha256":executor.contract.sha256},
                        config={"configurable":{"executor":executor},"recursion_limit":100})


def test_real_worktrees_parallel_coding_serial_verification_and_human_gate(local):
    executor,services,workers,verified,repo,review = local
    original = git(repo,"rev-parse","HEAD")
    result = run(executor)
    assert result["outcome"] == "awaiting_human_review"
    assert [stage for _,stage in workers.calls].count("green") == 2
    assert [stage for _,stage in workers.calls].count("refactor") == 2
    assert verified[0].candidate_revision == original
    assert verified[-1].full_suite is True
    assert review.state()["decision"] == "pending"
    assert git(repo,"rev-parse","HEAD") == original
    assert git(repo,"branch","--show-current") == "fixture/base"
    assert not git(services.integration.path,"status","--porcelain")
    test_unit = next(u for u in executor.contract.units if u.role=="test")
    assert all((services.integration.path / p).read_bytes()==b"baseline" for p in test_unit.owns)


def test_foreign_model_patch_never_reaches_integration(local):
    executor,services,workers,_,repo,_ = local
    workers.foreign=True
    with pytest.raises(ValueError):
        run(executor)
    assert not (services.integration.path / "shared.txt").exists()
    assert git(services.integration.path,"rev-parse","HEAD") == git(repo,"rev-parse","HEAD")


def test_preflight_failure_prevents_models_and_verification(local):
    executor,services,workers,verified,_,_ = local
    def fail():
        raise ValueError("Protected target differs")
    services.preflight=fail
    with pytest.raises(ValueError):
        run(executor)
    assert workers.calls == [] and verified == []


def test_verified_candidate_cannot_self_finalize(local):
    executor,services,_,_,_,_ = local
    run(executor)
    with pytest.raises(ValueError):
        services.step("finalize","unauthorized-finalize")


def test_completed_service_receipt_reconciles_without_repeating_work(local):
    executor,services,workers,_,_,_ = local
    executor.budget.begin_cycle(1,executor.contract.sha256,{u.id:executor.contract.lineage_for(u.id) for u in executor.contract.units})
    report = services.step("prepare","preparation")
    assert services.reconcile("prepare","preparation") == report
    with pytest.raises(ValueError):
        services.reconcile("code","unknown-effect")
