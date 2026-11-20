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
    if (contract.contract_version!=40
        or contract.sha256!='a0289951700127c2c1ac42cd1235f3dbf3359f7e7407c533025dba7c913ea15c'
        or result['outcome']!='operational'
        or result['candidate_revision']!='24edea5fe472e7f4e7623cc937b5acec80d42ab2'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v40-step2-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact anchor recovery identity changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    unit=next(u for u in contract.units if u.id=='TEST-PRES-NFR')
    originals={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v40-step2-prepare-TEST-PRES-NFR-TEST-PRES-NFR'
    if (state/('anchored-author/'+operation+'.complete.json')).exists():
        raise ValueError('Unexpected admission proof')
    receipts=[];last=''
    for suffix,digest,error in (
        ('','79e7a78e5e11e1080d682add9c53ac17623bdddbe9e8b4062f1d0f3b88b28e10','Model patch contains unowned path or invalid content'),
        ('-anchor-format-1','d248dba0acf5b71277cc5ad89a46b7976ae047748a6f2d222946476432f4cbf8','Model patch contains unowned path or invalid content')):
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
    workers.rejected_transport={unit.id:last}
    workers.authoring_clarifications={unit.id:'\nOWNERSHIP CLARIFICATION: repair-v17.md and its meta are NOT owned in this contract and MUST be omitted despite historical note hints. Update LobbyPresentationNfrTests.acceptance.md, which is actually owned. Keep the proposed real friendship setup in owned C# and every unread assertion. The last two responses were rejected wholly; no C# repair was applied.'}
    atomic_write(state,'recovery-authorizations/v40-nfr-unowned-note.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'settled_calls':receipts,'usage':budget.totals(),'human_accepted':False,
        'repair':'Same configured coder receives the actual rejected response and exact diagnostics; preserve all assertions and independent Sol review'},indent=2).encode())
    return True
