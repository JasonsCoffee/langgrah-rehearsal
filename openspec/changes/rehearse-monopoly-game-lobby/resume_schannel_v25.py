"""Exact direct-only retry after the first observed native TLS handshake failure."""
from hashlib import sha256
import json
from pathlib import Path
from operational_transport import retained_transport_failure,retained_key_limit_failure,retained_calibration_failure,retained_tls_probe_failure,retained_sol_review_failure
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def verify_author(state, integration, *, zero=False):
    operation='v25-step4-prepare-TEST-VIP-TEST-VIP' if zero else 'v25-step2-prepare-TEST-APPEAR-TEST-APPEAR'
    p=state/('anchored-author/'+operation+'.complete.json')
    d=json.loads(p.read_bytes())
    if d['actual_calls']!=[operation]:raise ValueError('Author call changed')
    for path,digest in d['file_sha256'].items():
        if sha256((integration/path).read_bytes()).hexdigest()!=digest:raise ValueError('Admitted coder file changed')


def reconcile(state,contract,budget,services,integration,settings,*,preconnect=False,zero=False):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=25 or contract.sha256!='7ddec8aafe4a7a4142523eeb2c4d09263ea935e94aad5604eecb8d9f46d1032d'
        or result['outcome']!='operational' or result['candidate_revision']!=('4cf732e5c8ca0640502ac87dd094cecfcf75cc9b' if zero else 'c9399302aea27a428e8185b0ad06fac7a24021b2')
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!=('v25-step4-prepare' if zero else ('v25-step3-prepare' if preconnect else 'v25-step2-prepare'))
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Direct recovery identity changed')
    if zero:
        call_id='v25-step4-prepare-review-TEST-VIP'
        record=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if (record.get('failure')!={'transport':'direct_preconnect','phase':'tls_establishment','failure_kind':'tls','input_tokens':0,'output_tokens':0}
            or budget._read()['calls'][call_id].get('actual')!=[0,0]
            or record['identity']['model']!=settings.judge.model):raise ValueError('Known pre-HTTP failure changed')
    if preconnect:
        proof=json.loads((state/'network-recovery/sol-preconnect-v25.json').read_bytes())
        if proof.get('calibration_verified') is not True or proof['models_config_sha256']!=sha256(Path('ai.local.toml').read_bytes()).hexdigest():
            raise ValueError('Direct TLS calibration or configured models changed')
    retained=[]
    for call_id,call in budget._read()['calls'].items():
        if 'actual' in call:continue
        receipt=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(receipt,call,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(receipt,call,16)
        elif call_id.startswith('judge-switch-v23-glm-json-review'):retained_calibration_failure(state,call_id,receipt,call)
        elif call_id.startswith('tls-recovery-v23-glm-json-review'):retained_tls_probe_failure(state,call_id,receipt,call)
        else:retained_sol_review_failure(state,call_id,receipt,call)
        retained.append(call_id)
    if len(retained)!=(10 if preconnect else 9):raise ValueError('Unknown reservation set changed')
    verify_author(state,integration,zero=zero)
    atomic_write(state,'recovery-authorizations/'+('v25-zero-tls-resume.json' if zero else ('v25-direct-preconnect-resume.json' if preconnect else 'v25-direct-schannel-retry.json')),json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],'usage':budget.totals(),
        'retained_uncertain':retained,'human_accepted':False,'network':'direct only; explicit user reply',
        'new_review_operation':'v25-step5-prepare-review-TEST-VIP' if zero else ('v25-step'+('4' if preconnect else '3')+'-prepare-review-TEST-APPEAR'),
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
    },indent=2).encode())
    return True
