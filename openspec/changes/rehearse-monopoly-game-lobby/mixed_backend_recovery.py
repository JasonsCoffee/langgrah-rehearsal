"""Read-only preservation guards for the exact retained operational boundary."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from unity_coder.core.contracts import Contract
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.local_executor import LocalExecutionServices
    from overlay_host import OverlayHost

CONTRACT='bbbfcf9dc2b51f1ffb9d8a935a1fbb72ca148ada5c2a89f6b37752065f9315e7'
CANDIDATE='625db77bf4e75060435947d955328a729f6f87dc'


def verify_preservation(before: dict,after: dict,frozen_before: dict[str,str],frozen_after: dict[str,str]) -> None:
    if (before.get('limits')!=after.get('limits') or not frozen_before or frozen_before!=frozen_after
        or any(after.get('calls',{}).get(call)!=value for call,value in before.get('calls',{}).items())
        or before.get('cycles')!=after.get('cycles')):
        raise ValueError('Run limits, historical charges, cycles or frozen bytes changed')


def validate_boundary(result: dict,evidence: dict,transaction: dict,pending: dict) -> None:
    request=evidence.get('request',{})
    if (result.get('run_id')!='monopoly-game-lobby' or result.get('outcome')!='operational'
        or result.get('contract_version')!=70 or result.get('contract_sha256')!=CONTRACT
        or result.get('candidate_revision')!=CANDIDATE or evidence.get('gate')!='tests'
        or evidence.get('status')!='failed' or request.get('request_id')!='v70-step8-verify'
        or request.get('candidate_revision')!=CANDIDATE or request.get('contract_sha256')!=CONTRACT
        or transaction.get('operation')!='v70-step8-verify' or transaction.get('stage')!='verify'
        or transaction.get('complete') is not True
        or pending.get('identity')!={'request':request,'unit':'ECON'} or 'result' in pending):
        raise ValueError('Only the exact stopped unresolved current boundary may change role policies')


def reconcile(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
              integration: Path,host: OverlayHost) -> bool:
    from codex_context_recovery import register_retained_call
    from operational_transport import retained_run_reservations
    from mixed_backend_policy import role_profile,profile_sha256
    from unity_coder.core.storage import atomic_write
    from unity_coder.core.workspaces import git
    run=state/'.agent/runs/monopoly-game-lobby';operation='v70-step8-verify';call=operation+'-judge-ECON'
    key=sha256(call.encode()).hexdigest();raw=(run/'model-calls'/(key+'.json')).read_bytes()
    evidence_raw=(run/'services-v70/evidence/v70-step8-verify.json').read_bytes();evidence=json.loads(evidence_raw)
    pending=services.effects.read('judge-'+operation+'-ECON')
    validate_boundary(json.loads((run/'result.json').read_bytes()),evidence,services.effects.read('transaction'),pending)
    if (sha256(raw).hexdigest()!='60b94160bfa531463581eccb61fc3a7d70f53f6388d898346da72c3ba09f6391'
        or sha256(evidence_raw).hexdigest()!='96e2194ac8ce7ccadc4bccccca11c9a6a3d480ed14d6f984162684653bd940bf'
        or contract.sha256!=CONTRACT or budget.limits!=role_profile()['limits']
        or git(integration,'rev-parse','HEAD').decode().strip()!=CANDIDATE or git(integration,'status','--porcelain')):
        raise ValueError('Original failed effect, candidate or limits changed')
    frozen=services.tdd._frozen_hashes;services.tdd.assert_frozen()
    if len(frozen)!=199 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!='2da65db6815d61fb277a19f826b4d512e78c8bc4dc2f4f8c4d1b3387e8d1c520':
        raise ValueError('Complete frozen lobby inventory changed')
    grant=json.loads((state/role_profile()['authorization_ref']).read_bytes())
    qualification=json.loads((state/'context-optimization/pilot-qualified.json').read_bytes())
    if (grant.get('profile_sha256')!=profile_sha256() or qualification.get('roles_qualified') is not True
        or qualification.get('profile_sha256')!=profile_sha256() or grant.get('candidate')!=CANDIDATE):
        raise ValueError('Exact current-candidate policy grant and genuine pilot required')
    preserved=json.loads((state/grant['preservation_ref']).read_bytes())
    verify_preservation(preserved['budget'],budget._read(),preserved['frozen'],frozen)
    ledger=budget._read();charge=ledger['calls'][call]
    if charge!={'reserved':[2694310,32768],'unit':'ECON','version':70}:
        raise ValueError('Entire latest unresolved Judge reservation required')
    historical=ledger|{'calls':{k:v for k,v in ledger['calls'].items() if k!=call}}
    if len(retained_run_reservations(state,historical))!=26:raise ValueError('Historical uncertain calls changed')
    register_retained_call(state,call,charge,sha256(raw).hexdigest())
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=27:raise ValueError('All 27 unknown reservations must remain')
    overlay=host.overlay.read()
    if overlay['candidate']!=CANDIDATE or overlay['baseline_sha256']!='12f3b9e07d8085e8ad0558e02223988c7313ac4392f77d9c80a91d8c6e6d74a0':
        raise ValueError('Original trusted overlay identity changed')
    for name,digest in {'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
        'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}.items():
        if sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:raise ValueError('Pinned overlay source changed')
    host.preflight();host.overlay.check(overlay)
    atomic_write(state,'recovery-authorizations/direct-deepseek-low-v70.json',json.dumps({
        'candidate':CANDIDATE,'contract_sha256':CONTRACT,'profile_sha256':profile_sha256(),
        'retained_uncertain':retained,'usage':budget.totals(),'historical_effects_unchanged':True,
        'new_operation_required':True,'human_accepted':False},indent=2).encode())
    return True
