"""Reconcile two exact settled responses rejected before patch admission."""
from hashlib import sha256
import json
from anchored_author import parse_anchored_patch
from noop_transport import normalize_identity_edits
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=36
        or contract.sha256!='5aeca09607116c5261eb2b70c834824998f69bcccb370551e3786cd487cbb809'
        or result['outcome']!='operational'
        or result['candidate_revision']!='2d7da890235b06ee90f91a39d45593f96a1f6ab2'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v36-step3-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact anchor recovery identity changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    unit=next(u for u in contract.units if u.id=='TEST-FRIEND-REQUESTS')
    originals={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v36-step3-prepare-TEST-FRIEND-REQUESTS-TEST-FRIEND-REQUESTS'
    if (state/('anchored-author/'+operation+'.complete.json')).exists():
        raise ValueError('Unexpected admission proof')
    receipts=[];last=''
    for suffix,digest,error in (
        ('','4e610a10ca7c72a50dc723bb776608a5301c6074c0eb66e2d11255b79b636d30','Anchor is absent or ambiguous'),
        ('-anchor-format-1','d0e1fc2b4302553241244fafcf97cdebb350e0b2a93d4d49a4d6b6bccd5791b9','Original replacements overlap')):
        call=operation+suffix
        raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes()
        if sha256(raw).hexdigest()!=digest:raise ValueError('Settled response changed')
        reply=json.loads(raw)['reply']
        if ledger['calls'][call].get('actual')!=[reply['input_tokens'],reply['output_tokens']]:
            raise ValueError('Charge changed')
        try:
            canonical,_=normalize_identity_edits(reply['text'],originals)
            parse_anchored_patch(canonical,unit.owns,originals)
        except ValueError as failure:
            if str(failure)!=error:raise
        else:raise ValueError('Expected rejected source transport')
        receipts.append({'call_id':call,'sha256':digest});last=reply['text']
    if services.tdd.state(unit.id).preparation_attempts!=2:
        raise ValueError('Preparation allowance changed')
    workers.rejected_transport={unit.id:last}
    atomic_write(state,'recovery-authorizations/v36-rejected-anchor.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'settled_calls':receipts,'usage':budget.totals(),'human_accepted':False,
        'repair':'Same configured coder receives the actual rejected response and exact diagnostics; preserve all assertions and independent Sol review'},indent=2).encode())
    return True
