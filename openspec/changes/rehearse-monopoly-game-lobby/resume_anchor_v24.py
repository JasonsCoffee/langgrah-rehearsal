"""Reconcile the exact completed, unapplied cycle-24 author-format stop."""
from hashlib import sha256
import json
from pathlib import Path
from anchored_author import parse_anchored_patch
from operational_transport import (
    retained_transport_failure, retained_key_limit_failure,
    retained_calibration_failure, retained_tls_probe_failure,
)
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile_anchor_stop(state, contract, budget, services, integration, settings):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    candidate='0230cd671319877bfa8f50b01a446beb547cc8db'
    if (contract.contract_version!=24
        or contract.sha256!='b2cfb1bd36c9a36589fcd023ca31d144487598a32e1ca57b76e7c6db4997e9ec'
        or result.get('outcome')!='operational' or result.get('candidate_revision')!=candidate
        or git(integration,'rev-parse','HEAD').decode().strip()!=candidate
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or settings.judge.model!='openai/gpt-6.1-sol'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Anchor recovery identity changed')
    transaction=services.effects.read('transaction')
    if not transaction.get('complete') or transaction.get('operation')!='v24-step3-prepare':
        raise ValueError('Author transaction is not durably complete')
    ledger=budget._read();retained=[];proof=[]
    records=run/'model-calls'
    for call_id,call in ledger['calls'].items():
        if 'actual' in call:continue
        receipt=json.loads((records/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(receipt,call,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(receipt,call,16)
        elif call_id.startswith('judge-switch-v23-glm-json-review'):retained_calibration_failure(state,call_id,receipt,call)
        elif call_id.startswith('tls-recovery-v23-glm-json-review'):retained_tls_probe_failure(state,call_id,receipt,call)
        else:raise ValueError('Unknown uncertain request')
        retained.append(call_id)
    if len(retained)!=6:raise ValueError('Retained reservation set changed')
    unit=next(u for u in contract.units if u.id=='TEST-APPEAR')
    sources={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v24-step3-prepare-TEST-APPEAR-TEST-APPEAR'
    for call_id in (operation,operation+'-anchor-format-1'):
        raw=(records/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
        record=json.loads(raw);reply=record.get('reply')
        if (not reply or ledger['calls'][call_id].get('actual')!=[reply['input_tokens'],reply['output_tokens']]
            or record['identity']['model']!=settings.coder.model):
            raise ValueError('Completed paid author evidence changed')
        try:parse_anchored_patch(reply['text'],unit.owns,sources)
        except ValueError as error:
            if str(error)!='Anchor is absent, ambiguous or unchanged':raise
        else:raise ValueError('Expected unapplied anchor failure')
        proof.append({'call_id':call_id,'receipt_sha256':sha256(raw).hexdigest()})
    if (state/('anchored-author/'+operation+'.complete.json')).exists():
        raise ValueError('Failed author unexpectedly has completion evidence')
    atomic_write(state,'recovery-authorizations/v24-anchor-format.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':candidate,'completed_paid_calls':proof,
        'retained_uncertain':retained,'usage':budget.totals(),'human_accepted':False,
        'diagnosis':'Both complete replies anchor an absent helper declaration. No patch admitted. Delegate a fresh operation against actual owned source; keep strict parsing and independent review.',
    },indent=2).encode())
    return True
