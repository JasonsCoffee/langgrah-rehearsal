"""Reconcile the settled and wholly unadmitted redundant NFR authoring effect."""
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING

from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

if TYPE_CHECKING:
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.contracts import Contract
    from unity_coder.core.local_executor import LocalExecutionServices


def reconcile(state: Path,contract: 'Contract',budget: 'BudgetLedger',
              services: 'LocalExecutionServices') -> bool:
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    candidate='fb5ae5ebe14d27cde693823127b982ea54d3c2c0'
    stage='v77-step3-prepare'
    unit_id='TEST-PRES-NFR'
    operation=stage+'-'+unit_id+'-'+unit_id
    source=services.integration.path
    tx=services.effects.read('transaction')
    pending=services.effects.read('worker-'+operation)
    if (contract.sha256!='60fbe79e1cf596fd26f01a203617ef55e46211c238a1e438758d01dc1b859e59'
        or result['outcome']!='operational' or result['candidate_revision']!=candidate
        or result['contract_sha256']!=contract.sha256
        or tx['operation']!=stage or not tx['complete']
        or git(source,'rev-parse','HEAD').decode().strip()!=candidate or git(source,'status','--porcelain')
        or pending!={'identity':{'stage':'test_authoring','unit':unit_id,'base':candidate}}
        or services.effects.read('apply-'+operation) is not None
        or (state/'anchored-author'/(operation+'.complete.json')).exists()
        or not services.state['feedback'].startswith('Independent Judge findings for TEST-APPEAR:')
        or services.tdd.frozen):
        raise ValueError('Exact unadmitted redundant NFR authoring boundary required')
    ledger=budget._read()
    retained_run_reservations(state,ledger)
    proof={}
    for call in (operation,operation+'-anchor-format-1'):
        raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes()
        record=json.loads(raw)
        identity,reply=record['identity'],record['reply']
        if (identity['call_id']!=call or identity['unit_id']!=unit_id
            or identity['role']!='coder' or identity['provider']!='deepseek'
            or ledger['calls'][call].get('actual')!=[reply['input_tokens'],reply['output_tokens']]):
            raise ValueError('Both redundant author replies must be settled and retained')
        proof[call]=sha256(raw).hexdigest()
    unit=next(item for item in contract.units if item.id==unit_id)
    if not services.workers.approved_review(unit,per_decision=True):
        raise ValueError('The exact NFR bytes require a positive independent review')
    atomic_write(state,'host-reconciliations/v77-redundant-nfr.json',json.dumps({
        'candidate':candidate,'contract_sha256':contract.sha256,'operation':operation,
        'retained_calls':proof,'patch_admitted':False,'next_scope':'TEST-APPEAR',
        'human_accepted':False},indent=2).encode())
    return True
