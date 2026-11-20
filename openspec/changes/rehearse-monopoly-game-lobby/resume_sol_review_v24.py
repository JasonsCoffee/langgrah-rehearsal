"""One exact same-judge retry; retain a completed admitted author patch."""
from hashlib import sha256
import json
from operational_transport import (
    retained_transport_failure, retained_key_limit_failure,
    retained_calibration_failure, retained_tls_probe_failure, retained_sol_review_failure,
)
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile_review_stop(state, contract, budget, services, integration, settings, *, schannel=False):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=24 or result['outcome']!='operational'
        or result['candidate_revision']!='cd868e9603a5aaf74509dabcdaff15394a893cf4'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or settings.judge.model!='openai/gpt-6.1-sol'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or not transaction['complete'] or transaction['operation']!=('v24-step5-prepare' if schannel else 'v24-step4-prepare')):
        raise ValueError('Sol review recovery identity changed')
    if schannel:
        calibration=json.loads((state/'network-recovery/sol-schannel-v24.json').read_bytes())
        if (calibration.get('calibration_verified') is not True
            or calibration.get('models_config_sha256')!=sha256(__import__('pathlib').Path('ai.local.toml').read_bytes()).hexdigest()):
            raise ValueError('Verified Schannel calibration is missing or config changed')
    preserved=[]
    for call_id,call in budget._read()['calls'].items():
        if 'actual' in call:continue
        receipt=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(receipt,call,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(receipt,call,16)
        elif call_id.startswith('judge-switch-v23-glm-json-review'):retained_calibration_failure(state,call_id,receipt,call)
        elif call_id.startswith('tls-recovery-v23-glm-json-review'):retained_tls_probe_failure(state,call_id,receipt,call)
        elif call_id in ('v24-step4-prepare-review-TEST-APPEAR','v24-step5-prepare-review-TEST-APPEAR'):retained_sol_review_failure(state,call_id,receipt,call)
        else:raise ValueError('Unexpected uncertain request')
        preserved.append(call_id)
    if len(preserved)!=(8 if schannel else 7):raise ValueError('Uncertain reservation set changed')
    verify_admitted_author(state,integration)
    atomic_write(state,'recovery-authorizations/'+('v24-sol-schannel-resume.json' if schannel else 'v24-sol-review-retry.json'),json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'usage':budget.totals(),'retained_uncertain':preserved,'human_accepted':False,
        'reuse':'Exact previously admitted coder patch, not a test-review approval',
        'new_judge_operation':'v24-step'+('6' if schannel else '5')+'-prepare-review-TEST-APPEAR',
    },indent=2).encode())
    return True


def verify_admitted_author(state, integration):
    proof=json.loads((state/'anchored-author/v24-step4-prepare-TEST-APPEAR-TEST-APPEAR.complete.json').read_bytes())
    if proof['actual_calls']!=['v24-step4-prepare-TEST-APPEAR-TEST-APPEAR']:
        raise ValueError('Unexpected admitted author identity')
    for path,digest in proof['file_sha256'].items():
        if sha256((integration/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Admitted coder file changed')
