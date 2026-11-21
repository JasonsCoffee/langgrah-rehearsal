"""Retain the exact unresolved Judge charge before a fresh native operation."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.contracts import Contract
    from unity_coder.core.local_executor import LocalExecutionServices
    from overlay_host import OverlayHost

CONTRACT='bbbfcf9dc2b51f1ffb9d8a935a1fbb72ca148ada5c2a89f6b37752065f9315e7'
CANDIDATE='be19106e61f8c5ce78cdde53803573616b9334fb'


def validate_stop(result: dict,evidence: dict,pending: dict,charge: dict,*,sdk_exists: bool) -> None:
    request=evidence['request']
    if (result.get('outcome')!='operational' or result.get('reason')!='Model transport requires reconciliation'
        or result.get('contract_version')!=70 or result.get('contract_sha256')!=CONTRACT
        or result.get('candidate_revision')!=CANDIDATE or evidence.get('gate')!='compile'
        or evidence.get('status')!='failed' or evidence.get('related_units')!=['ECON']
        or request.get('request_id')!='v70-step5-verify' or request.get('contract_sha256')!=CONTRACT
        or request.get('candidate_revision')!=CANDIDATE
        or pending.get('identity')!={'request':request,'unit':'ECON'} or 'result' in pending
        or charge!={'reserved':[934582,32768],'unit':'ECON','version':70} or sdk_exists):
        raise ValueError('Exact unresolved paid Judge stop and full reservation required')


def reconcile(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
              integration: Path,host: OverlayHost) -> bool:
    from codex_context_recovery import register_retained_call
    from operational_transport import retained_run_reservations
    from unity_coder.core.storage import atomic_write
    from unity_coder.core.workspaces import git
    run=state/'.agent/runs/monopoly-game-lobby';call='v70-step5-verify-judge-ECON';key=sha256(call.encode()).hexdigest()
    raw=(run/'model-calls'/(key+'.json')).read_bytes();record=json.loads(raw)
    evidence_raw=(run/'services-v70/evidence/v70-step5-verify.json').read_bytes();evidence=json.loads(evidence_raw)
    ledger=budget._read();charge=ledger['calls'][call]
    if (sha256(raw).hexdigest()!='20a4ec27b675a49414b6ddacea6c773953fb718904c710aaa6af86e7910251f6'
        or sha256(evidence_raw).hexdigest()!='256665687bfeea499594fab1268be0b4a878f3d1d10bb66a13c7331440ecda0d'
        or record.get('failure')!={} or record['identity'].get('model')!='gpt-6.1-sol'
        or record['identity'].get('effort')!='medium' or record['identity'].get('role')!='judge'):
        raise ValueError('Actual failed call or compiler evidence changed')
    validate_stop(json.loads((run/'result.json').read_bytes()),evidence,
        services.effects.read('judge-v70-step5-verify-ECON'),charge,
        sdk_exists=(state/'codex-receipts'/(key+'.json')).exists())
    transaction=services.effects.read('transaction')
    if (not transaction or transaction.get('operation')!='v70-step5-verify' or transaction.get('complete') is not True
        or contract.sha256!=CONTRACT or budget.limits!=[250000000,24000000,160,2]
        or git(integration,'rev-parse','HEAD').decode().strip()!=CANDIDATE or git(integration,'status','--porcelain')):
        raise ValueError('Completed stage, clean candidate and existing limits required')
    services.tdd.assert_frozen();frozen=services.tdd._frozen_hashes
    if len(frozen)!=199 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!='2da65db6815d61fb277a19f826b4d512e78c8bc4dc2f4f8c4d1b3387e8d1c520':
        raise ValueError('Complete frozen inventory changed')
    historical=ledger|{'calls':{k:v for k,v in ledger['calls'].items() if k!=call}}
    if len(retained_run_reservations(state,historical))!=25:raise ValueError('Historical reservations changed')
    register_retained_call(state,call,charge,sha256(raw).hexdigest())
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=26 or budget._read()['calls'][call]!=charge:raise ValueError('The unknown charge must remain in full')
    host.preflight()
    if host.overlay.read()['candidate']!=CANDIDATE:raise ValueError('Host candidate changed')
    atomic_write(state,'recovery-authorizations/v70-judge-step5-retained.json',json.dumps({
        'candidate':CANDIDATE,'contract_sha256':CONTRACT,'failed_call':call,'retained_charge':charge,
        'failed_receipt_sha256':sha256(raw).hexdigest(),'compile_evidence_sha256':sha256(evidence_raw).hexdigest(),
        'retained_uncertain':retained,'usage':budget.totals(),'new_native_operation_required':True,
        'original_effect_unchanged':True,'human_accepted':False},indent=2).encode())
    return True
