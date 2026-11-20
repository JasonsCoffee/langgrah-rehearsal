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
    if (contract.contract_version!=38
        or contract.sha256!='567173aaa0053bc4e77fb9815be8f6aedfa7d75cee33df3e17f5239a2c7e8232'
        or result['outcome']!='operational'
        or result['candidate_revision']!='12bc85e683f98ee7f34dbd147365c15d343dcd24'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v38-step5-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact anchor recovery identity changed')
    ledger=budget._read();retained_run_reservations(state,ledger)
    unit=next(u for u in contract.units if u.id=='TEST-CHAT')
    originals={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v38-step5-prepare-TEST-CHAT-TEST-CHAT'
    if (state/('anchored-author/'+operation+'.complete.json')).exists():
        raise ValueError('Unexpected admission proof')
    receipts=[];last=''
    for suffix,digest,error in (
        ('','074944159b10f82c0d20b1952c01954799618b7b052a7cc422db9228fb2602d0','Identity-only response cannot constitute a C# repair'),
        ('-anchor-format-1','2ac78feb866768f54918687c70f855e23d3332b1e5e10dd6d25218a4061f6910','Identity-only response cannot constitute a C# repair')):
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
    workers.full_file_authoring.add(unit.id)
    workers.authoring_clarifications={unit.id:'\nARCHITECT TDD CLARIFICATION: Your refusal reason confuses test expectations with business implementation. You are the TEST AUTHOR. Calling the actual prepared SOCIAL/SHELL services and asserting their SPECIFIED outcomes is required test implementation, even though the service stubs currently fail. Arrange accounts/messages/input state through the declared fake boundary, drive the real bound UI, then assert actual returned state and visible geometry against the specification. These tests SHOULD FAIL against nonfunctional production stubs. Do not wait for business implementation. Do not implement the service, return expected outcomes from a fake adapter, weaken assertions, or claim code exists only in notes. Strengthen all fourteen mapped methods and supply a truthful clause map. Use the actual read-only source-reviewed examples and declared APIs; declare only observation/input helpers in the owned partial. The fourteen test IDs and every source clause remain required.'}
    atomic_write(state,'recovery-authorizations/v38-chat-tdd-fullfile.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'settled_calls':receipts,'usage':budget.totals(),'human_accepted':False,
        'repair':'Same configured coder supplies its complete small owned source; strict ownership, syntax, actual C# change and independent Sol review remain'},indent=2).encode())
    return True
