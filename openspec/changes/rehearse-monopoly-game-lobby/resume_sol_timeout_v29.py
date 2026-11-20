"""One exact explicit paid retry, retaining the unknown Sol timeout charge."""
from hashlib import sha256
import json
from pathlib import Path
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings,*,coder=False):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=29 or contract.sha256!='bd3a914c6d189ae3ba2d3c12ea9827d9918bf876fe9e01b780bc8d19406a3e4e'
        or result['outcome']!='operational' or result['candidate_revision']!=('833c8e5b1b1467abb3713b1aead516b476b18fb7' if coder else '24fff9b3e767d55319dd6e8f4c46b1e8c5bd89a3')
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!=('v29-step7-prepare' if coder else 'v29-step2-prepare')
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Sol timeout recovery identity changed')
    retained=retained_run_reservations(state,budget._read())
    if services.tdd.state('TEST-PARTY' if coder else 'TEST-VIP').preparation_attempts:raise ValueError('Expected no rejection in this cycle')
    atomic_write(state,'recovery-authorizations/'+('v29-coder-body-timeout-retained.json' if coder else 'v29-sol-timeout-retained.json'),json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],
        'usage':budget.totals(),'retained_uncertain':retained,'human_accepted':False,
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
        'retry':'One explicit new native request; original full timeout reservation retained; models/policy/timeout unchanged'},indent=2).encode())
    return True
