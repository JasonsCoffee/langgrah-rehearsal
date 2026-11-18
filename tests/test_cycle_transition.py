"""Frozen same-run rework acceptance with interruption and resource continuity."""

import json
from dataclasses import replace

import pytest

from test_architect_boundary import planning, boundary, result
from test_contracts import bundle, load
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.dossiers import DossierUnit, emit_dossier
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.progress import ProgressStore


@pytest.fixture
def cycle(planning, tmp_path, bundle):
    b = boundary(planning, tmp_path)
    first = b.contract
    data, root = bundle
    data.update(contract_version=2, previous_contract_sha256=first.sha256)
    second = load(bundle, previous=first)
    budget = BudgetLedger(b.state_root, b.run_id, input_limit=100, output_limit=50, max_cycles=3, max_added_units=2)
    budget.begin_cycle(1, first.sha256, {u.id: first.lineage_for(u.id) for u in first.units})
    budget.reserve("old-call", "U1-state", 25, 10)
    progress = ProgressStore(b.state_root, b.run_id, contract_version=1, contract_sha256=first.sha256)
    progress.publish("rework", units={"U1-state": "contract"})
    emit_dossier(b.state_root, b.run_id, first, (DossierUnit("U1-state", "contract", "R7", "tests",
                 ("evidence/red.json",), "Missing contract detail", 1, ()),), budget_remaining={"input":75})
    result(b, "rework")
    lease = RunLease(b.state_root, b.run_id, "coordinator")
    lease.acquire(owner_alive=lambda _: False)
    context = discover_context(root, planning[0], sources=planning[1])
    return b, second, context, budget, lease


def advance(cycle, **kwargs):
    b, second, context, budget, lease = cycle
    return transition_cycle(b.planning_root, b.state_root, b.run_id, b.contract, second,
                            context, budget, lease, workers_reconciled=lambda: True, **kwargs)


def test_transition_preserves_usage_history_and_global_progress(cycle):
    b, second, context, budget, lease = cycle
    advance(cycle)
    current = ArchitectBoundary(b.planning_root, b.state_root, b.run_id, second, context).observe()
    assert current["result"] is None
    assert current["progress"]["contract_version"] == 2
    assert current["progress"]["sequence"] == 2
    assert budget.totals() == (25, 10)
    assert budget.unit_totals("U1-state") == (25, 10)
    archive = b.state_root / b.prefix / "cycles/v1"
    assert json.loads((archive / "result.json").read_bytes())["outcome"] == "rework"
    assert json.loads((archive / "invocation.json").read_bytes())["contract_sha256"] == b.contract.sha256
    assert (b.state_root / b.prefix / "dossier-v1.json").exists()
    advance(cycle)
    assert budget.totals() == (25, 10)
    assert current["progress"] == ArchitectBoundary(b.planning_root, b.state_root, b.run_id, second, context).observe()["progress"]
    lease.release()


@pytest.mark.parametrize("outcome", ["pass", "operational", "abandon", "cancelled", "awaiting_human_review"])
def test_only_finished_contract_rework_can_advance(cycle, outcome):
    b = cycle[0]
    record = result(b)
    record["outcome"] = outcome
    (b.state_root / b.prefix / "result.json").write_text(json.dumps(record))
    with pytest.raises(ValueError):
        advance(cycle)
    assert cycle[3].totals() == (25, 10)


def test_transition_requires_held_lease_and_reconciled_workers(cycle):
    b, second, context, budget, lease = cycle
    with pytest.raises(ValueError):
        transition_cycle(b.planning_root, b.state_root, b.run_id, b.contract, second, context,
                         budget, lease, workers_reconciled=lambda: False)
    lease.release()
    with pytest.raises(ValueError):
        advance(cycle)


def test_transition_rejects_skips_missing_dossier_and_wrong_budget(cycle):
    b, second, context, budget, lease = cycle
    with pytest.raises(ValueError):
        transition_cycle(b.planning_root,b.state_root,b.run_id,b.contract,replace(second,contract_version=3),
                         context,budget,lease,workers_reconciled=lambda:True)
    wrong = BudgetLedger(b.state_root,"another",input_limit=100,output_limit=50,max_cycles=3,max_added_units=2)
    with pytest.raises(ValueError):
        transition_cycle(b.planning_root,b.state_root,b.run_id,b.contract,second,context,wrong,lease,
                         workers_reconciled=lambda:True)
    (b.state_root / b.prefix / "dossier-v1.json").unlink()
    with pytest.raises(ValueError):
        advance(cycle)


def test_crash_after_budget_update_resumes_without_duplicate_cycle(cycle, monkeypatch):
    import unity_coder.core.cycles as module
    original = module.atomic_write
    def interrupted(root, path, content):
        if path.endswith("/invocation.json"):
            raise OSError("simulated crash")
        original(root,path,content)
    monkeypatch.setattr(module,"atomic_write",interrupted)
    with pytest.raises(OSError):
        advance(cycle)
    monkeypatch.setattr(module,"atomic_write",original)
    advance(cycle)
    b, second, context, budget, _ = cycle
    assert budget.totals() == (25,10)
    assert ArchitectBoundary(b.planning_root,b.state_root,b.run_id,second,context).observe()["result"] is None


def test_stopped_budget_cannot_begin_a_new_cycle(cycle):
    budget = cycle[3]
    budget.stop_for_budget(input_tokens=100)
    with pytest.raises(ValueError):
        advance(cycle)
    assert json.loads((cycle[0].state_root / budget.path).read_bytes())["cycles"].keys() == {"1"}
