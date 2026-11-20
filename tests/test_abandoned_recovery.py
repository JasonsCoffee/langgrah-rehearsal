"""Frozen acceptance for authenticated, crash-safe cycle-budget recovery."""
from dataclasses import replace
from hashlib import sha256
import json
import pytest
from test_architect_boundary import planning, boundary
from test_contracts import bundle, load
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.dossiers import emit_dossier
from unity_coder.core.lifecycle import RunLease, RunLifecycle
from unity_coder.core.progress import ProgressStore


@pytest.fixture
def stopped(planning, tmp_path, bundle):
    b = boundary(planning, tmp_path)
    data, root = bundle
    data.update(contract_version=2, previous_contract_sha256=b.contract.sha256)
    second = load(bundle, previous=b.contract, max_cycles=4)
    budget = BudgetLedger(b.state_root, b.run_id, input_limit=100, output_limit=50,
                          max_cycles=1, max_added_units=2)
    budget.begin_cycle(1, b.contract.sha256, {u.id:b.contract.lineage_for(u.id) for u in b.contract.units})
    budget.reserve('uncertain-old-call', 'U1-state', 25, 10)
    budget.stop_for_budget(cycle_exhausted=True)
    emit_dossier(b.state_root, b.run_id, b.contract, (), budget_remaining={'input_tokens':75}, reason='budget')
    outcome = RunLifecycle(b.state_root,b.run_id,contract_version=1,contract_sha256=b.contract.sha256).finish(
        'abandon',candidate_revision='retained-candidate',reason='budget',
        evidence_refs=(b.prefix+'/dossier-v1.json',))
    executor = dict(format_version=1,run_id=b.run_id,contract_version=1,contract_sha256=b.contract.sha256,
                    stage='ended',pending=None,steps=[{'stage':'prepare','result':outcome}])
    (b.state_root/b.prefix/'executor-v1.json').write_text(json.dumps(executor))
    ProgressStore(b.state_root,b.run_id,contract_version=1,contract_sha256=b.contract.sha256).publish('ended',units={})
    lease = RunLease(b.state_root,b.run_id,'trusted-operator')
    lease.acquire(owner_alive=lambda _:False)
    context = discover_context(root,planning[0],sources=planning[1])
    from unity_coder.core.recovery import RecoveryGrant
    grant = RecoveryGrant('recovery-1','human-operator','session/recovery-request',b.run_id,
                          b.contract.sha256,sha256((b.state_root/b.prefix/'result.json').read_bytes()).hexdigest(),4)
    yield b,second,context,budget,lease,grant
    if lease._held: lease.release()


def recover(stopped, **overrides):
    from unity_coder.core.recovery import recover_abandoned_run
    b,current,context,budget,lease,grant = stopped
    options = dict(credential='session-token', authenticate=lambda token:grant if token=='session-token' else None,
                   workers_reconciled=lambda:True, candidate_reconciled=lambda candidate:candidate=='retained-candidate')
    options.update(overrides)
    return recover_abandoned_run(b.planning_root,b.state_root,b.run_id,b.contract,current,
                                  context,budget,lease,**options)


def test_recovery_preserves_calls_usage_lineage_and_terminal_evidence(stopped):
    b,current,context,budget,lease,grant = stopped
    before = json.loads((b.state_root/budget.path).read_bytes())
    result_bytes = (b.state_root/b.prefix/'result.json').read_bytes()
    recover(stopped)
    after = json.loads((b.state_root/budget.path).read_bytes())
    assert after['calls'] == before['calls']
    assert after['cycles']['1'] == before['cycles']['1']
    assert after['limits'] == [100,50,4,2] and 'stopped' not in after
    assert after['cycles']['2']['sha256'] == current.sha256
    assert budget.totals() == (25,10)
    archive = b.state_root/b.prefix/'cycles/v1'
    assert (archive/'result.json').read_bytes() == result_bytes
    assert (archive/'budget.json').read_bytes() == json.dumps(before,sort_keys=True).encode()
    assert (archive/'executor-v1.json').exists() and (archive/'dossier-v1.json').exists()
    audit = json.loads((b.state_root/b.prefix/'recoveries/recovery-1.json').read_bytes())
    assert audit['state'] == 'complete' and audit['authorization']['actor'] == 'human-operator'
    assert 'session-token' not in json.dumps(audit)
    observation = ArchitectBoundary(b.planning_root,b.state_root,b.run_id,current,context).observe()
    assert observation['result'] is None and observation['progress']['sequence'] == 2
    recover(stopped)
    assert budget.totals() == (25,10)


@pytest.mark.parametrize('fault',['unauthorized','wrong_run','wrong_result','wrong_contract','no_growth','boolean_limit',
                                  'no_lease','workers','candidate','skip','changed_dossier','active_executor'])
def test_invalid_recovery_never_changes_budget(stopped,fault):
    b,current,context,budget,lease,grant = stopped
    initial = (b.state_root/budget.path).read_bytes()
    options = {}
    if fault == 'unauthorized': options['credential'] = 'untrusted'
    elif fault == 'wrong_run': stopped = (*stopped[:5],replace(grant,run_id='other'))
    elif fault == 'wrong_result': stopped = (*stopped[:5],replace(grant,result_sha256='0'*64))
    elif fault == 'wrong_contract': stopped = (*stopped[:5],replace(grant,previous_sha256='0'*64))
    elif fault == 'no_growth': stopped = (*stopped[:5],replace(grant,max_cycles=1))
    elif fault == 'boolean_limit': stopped = (*stopped[:5],replace(grant,max_cycles=True))
    elif fault == 'no_lease': lease.release()
    elif fault == 'workers': options['workers_reconciled'] = lambda:False
    elif fault == 'candidate': options['candidate_reconciled'] = lambda candidate:False
    elif fault == 'skip': stopped = (b,replace(current,contract_version=3),*stopped[2:])
    elif fault == 'changed_dossier':
        path=b.state_root/b.prefix/'dossier-v1.json'
        data=json.loads(path.read_bytes()); data['contract_sha256']='0'*64; path.write_text(json.dumps(data))
    else:
        path=b.state_root/b.prefix/'executor-v1.json'
        data=json.loads(path.read_bytes()); data['stage']='code'; path.write_text(json.dumps(data))
    with pytest.raises(ValueError): recover(stopped,**options)
    assert (b.state_root/budget.path).read_bytes() == initial


@pytest.mark.parametrize('failure_point',['archive','invocation','budget','complete'])
def test_interrupted_recovery_reconciles_without_reset_or_replay(stopped,monkeypatch,failure_point):
    import unity_coder.core.recovery as module
    b,current,context,budget,lease,grant = stopped
    real_write = module.atomic_write
    def fail(root,path,content):
        if ((failure_point=='archive' and '/cycles/' in path)
            or (failure_point=='invocation' and path.endswith('/invocation.json'))
            or (failure_point=='budget' and path.endswith('/budget.json'))
            or (failure_point=='complete' and '/recoveries/' in path and json.loads(content).get('state')=='complete')):
            raise OSError('simulated interruption')
        real_write(root,path,content)
    monkeypatch.setattr(module,'atomic_write',fail)
    with pytest.raises(OSError): recover(stopped)
    monkeypatch.setattr(module,'atomic_write',real_write)
    recover(stopped)
    assert budget.totals() == (25,10)
    ledger=json.loads((b.state_root/budget.path).read_bytes())
    assert set(ledger['calls']) == {'uncertain-old-call'} and set(ledger['cycles']) == {'1','2'}
    assert ArchitectBoundary(b.planning_root,b.state_root,b.run_id,current,context).observe()['result'] is None


def test_pending_recovery_rejects_changed_authorization(stopped,monkeypatch):
    import unity_coder.core.recovery as module
    real_write=module.atomic_write
    def fail(root,path,content):
        if '/cycles/' in path: raise OSError('interrupted')
        real_write(root,path,content)
    monkeypatch.setattr(module,'atomic_write',fail)
    with pytest.raises(OSError): recover(stopped)
    monkeypatch.setattr(module,'atomic_write',real_write)
    changed=(*stopped[:5],replace(stopped[5],max_cycles=5))
    with pytest.raises(ValueError): recover(changed)
    assert stopped[3].totals() == (25,10)


@pytest.mark.parametrize('fault',['other_outcome','token_exhaustion','archive_conflict','foreign_budget','unconsumed_cycles'])
def test_recovery_rejects_incompatible_stop_and_resources(stopped,fault):
    b,current,context,budget,lease,grant=stopped
    if fault=='other_outcome':
        path=b.state_root/b.prefix/'result.json'
        record=json.loads(path.read_bytes()); record['outcome']='cancelled'; path.write_text(json.dumps(record))
        stopped=(*stopped[:5],replace(grant,result_sha256=sha256(path.read_bytes()).hexdigest()))
    elif fault in ('token_exhaustion','unconsumed_cycles'):
        path=b.state_root/budget.path
        record=json.loads(path.read_bytes())
        if fault=='token_exhaustion': record['calls']['uncertain-old-call']['actual']=[100,50]
        else: record['limits'][2]=3; budget.limits[2]=3
        path.write_text(json.dumps(record,sort_keys=True))
    elif fault=='archive_conflict':
        path=b.state_root/b.prefix/'cycles/v1/result.json'; path.parent.mkdir(parents=True); path.write_bytes(b'conflict')
    else:
        other=BudgetLedger(b.state_root,'foreign',input_limit=100,output_limit=50,max_cycles=1,max_added_units=2)
        stopped=(*stopped[:3],other,*stopped[4:])
    before=(b.state_root/budget.path).read_bytes()
    with pytest.raises(ValueError): recover(stopped)
    assert (b.state_root/budget.path).read_bytes()==before
