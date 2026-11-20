"""Reconcile the exact second format failure; select bounded small-file transport."""
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
        or not transaction['complete'] or transaction['operation']!='v36-step4-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact anchor recovery identity changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    unit=next(u for u in contract.units if u.id=='TEST-FRIEND-REQUESTS')
    originals={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v36-step4-prepare-TEST-FRIEND-REQUESTS-TEST-FRIEND-REQUESTS'
    if (state/('anchored-author/'+operation+'.complete.json')).exists():
        raise ValueError('Unexpected admission proof')
    receipts=[];last=''
    for suffix,digest,error in (
        ('','9919900454b9cde4043e9e441ce7ad141863ea9e828b044049d65980bc53b39e','Original replacements overlap'),
        ('-anchor-format-1','61c460356a3a464927381bb9caeaa23a6b92c9f49eb97a30b092524a9a39a96b','Identity-only response cannot constitute a C# repair')):
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
    workers.full_file_authoring={unit.id}
    atomic_write(state,'recovery-authorizations/v36-focused-fullfile.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'settled_calls':receipts,'usage':budget.totals(),'human_accepted':False,
        'repair':'Same configured coder supplies its complete small owned source; strict ownership, syntax, actual C# change and independent Sol review remain'},indent=2).encode())
    return True
