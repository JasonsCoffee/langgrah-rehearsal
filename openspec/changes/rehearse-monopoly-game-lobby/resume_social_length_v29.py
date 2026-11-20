"""Recover a settled truncated response without admitting any partial source."""
from hashlib import sha256
import json
from pathlib import Path
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=29 or contract.sha256!='bd3a914c6d189ae3ba2d3c12ea9827d9918bf876fe9e01b780bc8d19406a3e4e'
        or result['outcome']!='operational' or result['candidate_revision']!='be76b805c12cc33862af4a4b5135b75e271dc8bc'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v29-step11-prepare'
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Length recovery identity changed')
    call_id='v29-step11-prepare-TEST-SOCIAL-TEST-SOCIAL'
    raw=(run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes();record=json.loads(raw)
    failure=record.get('failure',{})
    if (sha256(raw).hexdigest()!='9df62a97e9d0503bcd38837932c44c42c1860905c0b310db0fcbbfec05b54af3'
        or failure.get('finish_reason')!='length'
        or budget._read()['calls'][call_id].get('actual')!=[75795,65536]
        or 'reply' in record or services.tdd.state('TEST-SOCIAL').preparation_attempts!=1
        or (state/('anchored-author/'+call_id+'.complete.json')).exists()):
        raise ValueError('Settled truncated response or source counter changed')
    retained=retained_run_reservations(state,budget._read())
    atomic_write(state,'recovery-authorizations/v29-social-json-length.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],'original_call':call_id,
        'receipt_sha256':sha256(raw).hexdigest(),'actual_usage':[75795,65536],
        'partial_content_sha256':sha256(failure.get('partial_content','').encode()).hexdigest(),
        'partial_content_applied':False,'retained_uncertain':retained,'usage':budget.totals(),
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),'human_accepted':False,
        'repair':'Same coder, approved authoring allocation, native-job JSON mode and final hash-bound edit protocol; no budget/output reset or partial source recovery'},indent=2).encode())
    return True
