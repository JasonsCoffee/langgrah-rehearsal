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
    if (contract.contract_version!=37
        or contract.sha256!='e108984439bae2a345fc535f4acd73305fbf1e9ae56013d357e55efa9dbecb14'
        or result['outcome']!='operational'
        or result['candidate_revision']!='b9e0a149e42c07ae76b93ab46f62dcee828f243e'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v37-step2-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact anchor recovery identity changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    unit=next(u for u in contract.units if u.id=='TEST-PARTNER-RECS')
    originals={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v37-step2-prepare-TEST-PARTNER-RECS-TEST-PARTNER-RECS'
    if (state/('anchored-author/'+operation+'.complete.json')).exists():
        raise ValueError('Unexpected admission proof')
    receipts=[];last=''
    for suffix,digest,error in (
        ('','ca08e8fa50e37525c6e6a368587cf74f1aef9ac7224fb2ff2d899f69c3fb88b1','Absent or duplicate source'),
        ('-anchor-format-1','61f35823e8078c0597b19e5dbd43e050028b42d3500ae543912aa779f007bbee','Absent or duplicate source')):
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
    if services.tdd.state(unit.id).preparation_attempts!=1:
        raise ValueError('Preparation allowance changed')
    workers.full_file_authoring.add(unit.id)
    atomic_write(state,'recovery-authorizations/v37-partners-focused-fullfile.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'settled_calls':receipts,'usage':budget.totals(),'human_accepted':False,
        'repair':'Same configured coder supplies its complete small owned source; strict ownership, syntax, actual C# change and independent Sol review remain'},indent=2).encode())
    return True
