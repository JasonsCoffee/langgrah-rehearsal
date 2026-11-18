"""Frozen production dispatch contract; services are trusted offline boundaries."""

from dataclasses import asdict
import json

import pytest

from test_contracts import bundle, load
from unity_coder.core.executor import ProductionExecutor, StepResult
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease, RunLifecycle
from unity_coder.graph import graph


class Services:
    def __init__(self, contract, root):
        self.contract, self.root = contract, root
        self.calls = []
        self.next = {"prepare":"red", "red":"code", "code":"verify", "verify":"refactor",
                     "refactor":"final_verify", "final_verify":"review"}

    def step(self, stage, operation_id):
        self.calls.append((stage, operation_id))
        if stage == "review":
            record = RunLifecycle(self.root,"run",contract_version=1,contract_sha256=self.contract.sha256).finish(
                "awaiting_human_review",candidate_revision="candidate",reason="verified",evidence_refs=("evidence/test.json",))
            return StepResult("ended", {"U1-state":"complete"}, record)
        return StepResult(self.next[stage], {"U1-state":stage})

    def reconcile(self, stage, operation_id):
        raise ValueError("Unknown external operation; no replay")


@pytest.fixture
def executor(bundle):
    c = load(bundle)
    root = bundle[1] / "state"
    budget = BudgetLedger(root,"run",input_limit=1000,output_limit=500,max_cycles=3,max_added_units=2)
    lease = RunLease(root,"run","host")
    lease.acquire(owner_alive=lambda _:False)
    services = Services(c,root)
    return ProductionExecutor(root,"run",c,budget,lease,services), services, budget


def invoke(executor):
    return graph.invoke({"run_id":"run", "contract_sha256":executor.contract.sha256},
                        config={"configurable":{"executor":executor}})


def test_exported_graph_dispatches_real_stage_order_and_stops_for_review(executor):
    worker, services, budget = executor
    result = invoke(worker)
    assert [s for s,_ in services.calls] == ["prepare","red","code","verify","refactor","final_verify","review"]
    assert result["outcome"] == "awaiting_human_review"
    assert budget.totals() == (0,0)
    assert len({operation for _,operation in services.calls}) == 7
    before = list(services.calls)
    invoke(worker)
    assert services.calls == before


def test_graph_requires_trusted_runtime_and_matching_identity(executor):
    with pytest.raises(ValueError):
        graph.invoke({"run_id":"run","contract_sha256":"hash"})
    worker, services, _ = executor
    with pytest.raises(ValueError):
        graph.invoke({"run_id":"foreign","contract_sha256":worker.contract.sha256},
                     config={"configurable":{"executor":worker}})
    assert services.calls == []


def test_illegal_skip_cannot_bypass_red_or_final_suite(executor):
    worker, services, _ = executor
    services.next["prepare"] = "review"
    with pytest.raises(ValueError,match="transition"):
        invoke(worker)
    assert [s for s,_ in services.calls] == ["prepare"]


def test_checkpoint_resume_does_not_repeat_completed_stages(executor):
    worker, services, budget = executor
    worker.advance("prepare")
    worker.advance("red")
    restarted = ProductionExecutor(worker.root,worker.run_id,worker.contract,budget,worker.lease,services)
    invoke(restarted)
    assert [s for s,_ in services.calls].count("prepare") == 1
    assert [s for s,_ in services.calls].count("red") == 1


def test_pending_effect_requires_reconciliation_not_blind_dispatch(executor):
    worker, services, budget = executor
    original = services.step
    def crash(stage,operation):
        original(stage,operation)
        raise OSError("interrupted after effect")
    services.step = crash
    with pytest.raises(OSError):
        worker.advance("prepare")
    services.step = original
    with pytest.raises(ValueError,match="no replay"):
        invoke(ProductionExecutor(worker.root,worker.run_id,worker.contract,budget,worker.lease,services))
    assert len(services.calls) == 1


def test_forged_terminal_return_requires_durable_result(executor):
    worker, services, _ = executor
    services.step = lambda stage, operation: StepResult("ended",{}, {"outcome":"pass"})
    with pytest.raises(ValueError):
        invoke(worker)


def test_lease_and_frozen_contract_references_are_checked_before_dispatch(executor,bundle):
    worker, services, _ = executor
    worker.lease.release()
    with pytest.raises(ValueError):
        invoke(worker)
    assert services.calls == []


def test_failed_verification_routes_bounded_repair_through_code(executor):
    worker, services, _ = executor
    original = services.step
    failures = []
    def repair(stage,operation):
        if stage == "verify" and not failures:
            failures.append(True)
            services.calls.append((stage,operation))
            return StepResult("code",{"U1-state":"repair"})
        return original(stage,operation)
    services.step = repair
    invoke(worker)
    assert [s for s,_ in services.calls].count("code") == 2
    assert [s for s,_ in services.calls].count("refactor") == 1
