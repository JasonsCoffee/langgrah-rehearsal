"""Recover the exact coder connection failure without changing coder policy."""
from hashlib import sha256
import json
from pathlib import Path
from operational_transport import retained_transport_failure,retained_key_limit_failure,retained_calibration_failure,retained_tls_probe_failure,retained_sol_review_failure,retained_coder_connection_failure
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=25 or contract.sha256!='7ddec8aafe4a7a4142523eeb2c4d09263ea935e94aad5604eecb8d9f46d1032d'
        or result['outcome']!='operational' or result['candidate_revision']!='2947e6268eae0301123f78688276bcc83f624720'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v25-step8-prepare'
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.coder.upstream_provider!='alibaba'):
        raise ValueError('Coder network recovery identity changed')
    retained=[]
    for call_id,call in budget._read()['calls'].items():
        if 'actual' in call:continue
        receipt=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(receipt,call,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(receipt,call,16)
        elif call_id.startswith('judge-switch-v23-glm-json-review'):retained_calibration_failure(state,call_id,receipt,call)
        elif call_id.startswith('tls-recovery-v23-glm-json-review'):retained_tls_probe_failure(state,call_id,receipt,call)
        elif call_id=='v25-step8-prepare-TEST-MATCH-TEST-MATCH':retained_coder_connection_failure(state,call_id,receipt,call)
        else:retained_sol_review_failure(state,call_id,receipt,call)
        retained.append(call_id)
    if len(retained)!=11:raise ValueError('Uncertain reservation set changed')
    if (state/'anchored-author/v25-step8-prepare-TEST-MATCH-TEST-MATCH.complete.json').exists():raise ValueError('Failed coder unexpectedly has admission proof')
    if services.tdd.state('TEST-MATCH').preparation_attempts!=2:raise ValueError('Preparation counter changed')
    policy={'format_version':1,'profile':'verified_direct_preconnect','automatic_retries':0,
        'certificate_verification':'required','tls_establishment_attempts':3}
    atomic_write(state,'network-policy.coder-preconnect.json',json.dumps(policy,indent=2).encode())
    atomic_write(state,'recovery-authorizations/v25-coder-direct-setup.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],'usage':budget.totals(),
        'retained_uncertain':retained,'human_accepted':False,'network':'direct only',
        'new_coder_operation':'v25-step9-prepare-TEST-MATCH-TEST-MATCH',
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
        'model_provider_effort_temperature_unchanged':True,
    },indent=2).encode())
    return True
