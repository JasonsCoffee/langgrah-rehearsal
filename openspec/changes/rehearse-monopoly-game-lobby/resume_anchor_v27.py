"""Reconcile the exact two settled, unapplied ambiguous-anchor responses."""
from hashlib import sha256
import json
from pathlib import Path
from anchored_author import parse_anchored_patch
from operational_transport import retained_transport_failure,retained_key_limit_failure,retained_calibration_failure,retained_tls_probe_failure,retained_sol_review_failure,retained_coder_connection_failure
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=27 or contract.sha256!='00919976e1d4cd3738a88acec9d007cf8f89a642d734f1732bb0127832643705'
        or result['outcome']!='operational' or result['candidate_revision']!='0c65fda2a7f0660bf685e8e554f0de51ba802fe5'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v27-step8-prepare'
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Anchor reconciliation identity changed')
    ledger=budget._read();retained=[]
    for call_id,call in ledger['calls'].items():
        if 'actual' in call:continue
        record=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(record,call,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(record,call,16)
        elif call_id.startswith('judge-switch-v23-glm-json-review'):retained_calibration_failure(state,call_id,record,call)
        elif call_id.startswith('tls-recovery-v23-glm-json-review'):retained_tls_probe_failure(state,call_id,record,call)
        elif call_id=='v25-step8-prepare-TEST-MATCH-TEST-MATCH':retained_coder_connection_failure(state,call_id,record,call)
        else:retained_sol_review_failure(state,call_id,record,call)
        retained.append(call_id)
    if len(retained)!=11:raise ValueError('Uncertain reservations changed')
    unit=next(u for u in contract.units if u.id=='TEST-PARTY')
    sources={p:(integration/p).read_bytes().decode('utf-8') for p in unit.owns if p.endswith('.cs')}
    operation='v27-step8-prepare-TEST-PARTY-TEST-PARTY';receipts=[];last=''
    if (state/('anchored-author/'+operation+'.complete.json')).exists():raise ValueError('Unapplied patch has admission proof')
    for call_id in (operation,operation+'-anchor-format-1'):
        raw=(run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes();record=json.loads(raw);reply=record['reply']
        if ledger['calls'][call_id].get('actual')!=[reply['input_tokens'],reply['output_tokens']]:raise ValueError('Settled charge changed')
        try:parse_anchored_patch(reply['text'],unit.owns,sources)
        except ValueError as error:
            if str(error)!='Anchor is absent, ambiguous or unchanged':raise
        else:raise ValueError('Expected invalid delegated anchors')
        receipts.append({'call_id':call_id,'sha256':sha256(raw).hexdigest()});last=reply['text']
    if services.tdd.state(unit.id).preparation_attempts!=2:raise ValueError('Preparation counter changed')
    workers.rejected_transport={unit.id:last}
    atomic_write(state,'recovery-authorizations/v27-ambiguous-anchor.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],'settled_calls':receipts,
        'usage':budget.totals(),'retained_uncertain':retained,'human_accepted':False,
        'repair':'Supply actual rejected transport and occurrence counts to the same configured coder; keep strict parsing and actual Sol review',
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest()},indent=2).encode())
    return True
