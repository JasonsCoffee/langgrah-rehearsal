import json
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from test_branches import setup
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.governor import BudgetGovernor


def prepare(workspace,tmp_path):
    manager,repo,base,integration,candidate=setup(workspace,tmp_path)
    root=tmp_path/'state'
    ledger=BudgetLedger(root,'run1',input_limit=100,output_limit=50,max_cycles=3,max_added_units=2)
    ledger.begin_cycle(1,manager.contract.sha256,{u.id:(u.id,) for u in manager.contract.units})
    ledger.reserve('spent','U1-state',100,50)
    return BudgetGovernor(manager,integration,ledger),ledger,repo,base,candidate,integration


def test_budget_abandon_stops_calls_retains_candidate_and_writes_dossier(workspace,tmp_path):
    governor,ledger,repo,base,candidate,integration=prepare(workspace,tmp_path)
    result=governor.abandon(reconcile_workers=lambda:True)
    assert result['outcome']=='abandon' and result['reason']=='budget'
    assert result['candidate_revision']==candidate
    assert git(integration.path,'rev-parse','HEAD')==base
    assert git(repo,'rev-parse',integration.branch)==candidate
    dossier=json.loads((ledger.root/result['evidence_refs'][0]).read_bytes())
    assert dossier['reason']=='budget' and dossier['failed_units']==[]
    ledger.reconcile('spent',1,1)
    with pytest.raises(ValueError): ledger.reserve('late','U1-state',1,1)


def test_unreconciled_workers_prevent_git_transition(workspace,tmp_path):
    governor,ledger,repo,base,candidate,integration=prepare(workspace,tmp_path)
    with pytest.raises(ValueError): governor.abandon(reconcile_workers=lambda:False)
    assert git(integration.path,'rev-parse','HEAD')==candidate
    ledger.reconcile('spent',1,1)
    with pytest.raises(ValueError): ledger.reserve('late','U1-state',1,1)
    assert governor.abandon(reconcile_workers=lambda:True)['outcome']=='abandon'


def test_cannot_manufacture_budget_abandon_with_available_allowance(workspace,tmp_path):
    governor,ledger,repo,base,candidate,integration=prepare(workspace,tmp_path)
    ledger.reconcile('spent',1,1)
    with pytest.raises(ValueError): governor.abandon(reconcile_workers=lambda:True)
    assert git(integration.path,'rev-parse','HEAD')==candidate


def test_abandon_resume_is_idempotent_after_usage_reconciliation(workspace,tmp_path):
    governor,ledger,repo,base,candidate,integration=prepare(workspace,tmp_path)
    first=governor.abandon(reconcile_workers=lambda:True)
    ledger.reconcile('spent',1,1)
    assert governor.abandon(reconcile_workers=lambda:True)==first
