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
    confirmation=json.loads((state/'model-authorizations/sol-key-allowance-restored-v51.json').read_bytes())
    expected_reply='Change the name of "Sol" to Judge. Add used AI model and effort to the components using them, such as Judge(Sol), or Coder(DS4.1 Flash, low), etc. And allowance is restored.'
    if (confirmation.get('reply')!=expected_reply or not confirmation.get('provenance')
        or confirmation.get('allowance_restored') is not True):
        raise ValueError('Explicit provider restoration confirmation required')
    if (contract.contract_version!=51
        or contract.sha256!='3ed35231482ffa193e9502979fe1d71d397673fc33f5e7d3fa449ca13e10417f'
        or result['outcome']!='operational'
        or result['candidate_revision']!='a21e01720dacd61d3604adca068f0b7a50e8ce6c'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v51-step4-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact Sol allowance recovery identity changed')
    ledger=budget._read();retained=retained_run_reservations(state,ledger)
    proof=json.loads((state/'anchored-author/v51-step4-prepare-TEST-SOCIAL-TEST-SOCIAL.complete.json').read_bytes())
    if (proof['contract_sha256']!=contract.sha256 or proof['unit']!='TEST-SOCIAL'
        or proof['actual_calls']!=['v51-step4-prepare-TEST-SOCIAL-TEST-SOCIAL']):
        raise ValueError('Admitted coder proof changed')
    for path,digest in proof['file_sha256'].items():
        if sha256((integration/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Admitted coder source changed')
    call=proof['actual_calls'][0]
    reply=json.loads((run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes())['reply']
    if ledger['calls'][call].get('actual')!=[reply['input_tokens'],reply['output_tokens']]:
        raise ValueError('Settled coder charge changed')
    if services.tdd.state('TEST-SOCIAL').preparation_attempts!=1:
        raise ValueError('Preparation count changed')
    unit=next(u for u in contract.units if u.id=='TEST-SOCIAL')
    hashes={p:sha256((integration/p).read_bytes()).hexdigest() for p in unit.owns}
    workers.reconciled_worker_patch={'unit':unit.id,
        'operation':'v51-step5-prepare-TEST-SOCIAL-TEST-SOCIAL',
        'source_sha256':hashes,'files':{},
        'reason':'Reuse the exact admitted paid author source after retained HTTP-403 judge failure; actual independent Sol review is still required'}
    atomic_write(state,'recovery-authorizations/v51-sol-key-allowance-resume.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'retained_uncertain':retained,'usage':budget.totals(),'source_sha256':hashes,
        'confirmation':confirmation,'human_accepted':False,
        'next_judge_call':'v51-step5-prepare-review-TEST-SOCIAL'},indent=2).encode())
    return True
