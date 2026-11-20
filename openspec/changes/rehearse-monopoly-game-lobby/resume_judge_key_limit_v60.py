"""One exact public resume after confirmed provider allowance restoration."""
from hashlib import sha256
import json
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    confirmation=json.loads((state/'model-authorizations/judge-key-allowance-restored-v60.json').read_bytes())
    expected_reply='Allowance restored; retry the same run'
    if (confirmation.get('reply')!=expected_reply or not confirmation.get('provenance')
        or confirmation.get('allowance_restored') is not True):
        raise ValueError('Explicit provider restoration confirmation required')
    if (contract.contract_version!=60
        or contract.sha256!='5597cb71b2157b83cb4ee618133ba0cf9d708de54542479474f712173d1e7012'
        or result['outcome']!='operational'
        or result['candidate_revision']!='0519b568003ae4f820122ec8ef94016a068597f2'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v60-step4-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact Judge allowance recovery identity changed')
    ledger=budget._read();retained=retained_run_reservations(state,ledger)
    from full_file_admission import admitted_full_file
    unit=next(u for u in contract.units if u.id=='TEST-CHAT-STATE')
    proof=admitted_full_file(state,60,'v60-step4-prepare',unit.id,unit.owns,result['candidate_revision'],integration,ledger,contract.sha256)
    if services.tdd.state('TEST-CHAT-STATE').preparation_attempts!=1:
        raise ValueError('Preparation count changed')
    unit=next(u for u in contract.units if u.id=='TEST-CHAT-STATE')
    hashes={p:sha256((integration/p).read_bytes()).hexdigest() for p in unit.owns}
    workers.reconciled_worker_patch={'unit':unit.id,
        'operation':'v60-step5-prepare-TEST-CHAT-STATE-TEST-CHAT-STATE',
        'source_sha256':hashes,'files':{},
        'reason':'Reuse the exact admitted paid author source after retained HTTP-403 judge failure; actual independent Judge review is still required'}
    atomic_write(state,'recovery-authorizations/v60-judge-key-allowance-resume.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'retained_uncertain':retained,'usage':budget.totals(),'source_sha256':hashes,
        'confirmation':confirmation,'human_accepted':False,
        'next_judge_call':'v60-step5-prepare-review-TEST-CHAT-STATE'},indent=2).encode())
    return True
