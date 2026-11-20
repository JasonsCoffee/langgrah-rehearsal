"""Reconcile an exact host-only failure before model reservation or dispatch."""
from hashlib import sha256
import json
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def reconcile(state, contract, budget, services, integration):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    candidate='6003cd2d6a2031027ad0ed6c17ff49fe51d17233'
    if (contract.contract_version!=31
        or contract.sha256!='74d6c7a1a5b3527e413ee59e0bb1ad4003c76c5548ed094d39a46481ab3e6eed'
        or result['outcome']!='operational' or result['candidate_revision']!=candidate
        or git(integration,'rev-parse','HEAD').decode().strip()!=candidate
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or transaction['operation']!='v31-step1-prepare' or not transaction['complete']):
        raise ValueError('Host-only recovery identity changed')
    ledger=budget._read()
    retained_run_reservations(state,ledger)
    if any(call.startswith('v31-') for call in ledger['calls']):
        raise ValueError('A model reservation exists; no host-only recovery')
    for path in (run/'model-calls').glob('*.json'):
        if json.loads(path.read_bytes())['identity']['call_id'].startswith('v31-'):
            raise ValueError('A model effect exists; no host-only recovery')
    story=next(path for path in (integration/'specs/monopoly-game-lobby/sources').glob('*.md')
               if path.name.endswith('\u7528\u6237\u6545\u4e8b.md'))
    source=next(path for path in (integration/'specs/monopoly-game-lobby/sources').glob('*.md')
                if path.name.endswith('\u9700\u6c42\u5206\u6790.md'))
    if not story.is_file() or not source.is_file():raise ValueError('Protected sources missing')
    atomic_write(state,'recovery-authorizations/v31-context-before-model.json',json.dumps({
        'candidate':candidate,'contract_sha256':contract.sha256,'usage':budget.totals(),
        'reason':'Reversed accidental host-only UTF-8/GBK path conversion; original exported source files were present and unchanged',
        'source_sha256':{path.name:sha256(path.read_bytes()).hexdigest() for path in (story,source)},
        'no_model_calls_or_reservations_in_failed_step':True,'human_accepted':False},indent=2).encode())
    return True
