"""Retain uncertain paid effects before the next native budget reservation."""
from hashlib import sha256
import json
from pathlib import Path
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state,contract,budget,services,integration,settings):
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=28 or contract.sha256!='1419cad6f2744dabef7e8a5b337e688e6c7af9e2b332dfca497220fef23c3535'
        or result['outcome']!='operational' or result['candidate_revision']!='05817457df96f940a927e703b604dabca4fdf7d7'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v28-step5-prepare'
        or settings.judge.model!='openai/gpt-6.1-sol' or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Post-request recovery identity changed')
    retained=retained_run_reservations(state,budget._read())
    if (state/'anchored-author/v28-step5-prepare-TEST-QUEUE-TEST-QUEUE.complete.json').exists():raise ValueError('Failed request unexpectedly has admission proof')
    atomic_write(state,'recovery-authorizations/v28-post-request-retained.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],
        'usage':budget.totals(),'retained_uncertain':retained,'human_accepted':False,
        'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
        'retry':'New native operation only after reconciliation; original full reservation retained; next reservation remains subject to active limits'},indent=2).encode())
    return True
