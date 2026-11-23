"""One proof-bound native retry after exact zero-submission Bridge discovery."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
from mixed_backend_recovery import CONTRACT,CANDIDATE,verify_preservation
from lobby_readiness_wait import DISCOVERY_ERROR,ticket_path
from unity_coder.core.verification import VerificationRequest
if TYPE_CHECKING:
    from unity_coder.core.contracts import Contract
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.local_executor import LocalExecutionServices
    from overlay_host import OverlayHost


def validate_stop(result: dict,evidence: dict,transaction: dict,compiled: dict,*,submitted: bool) -> None:
    wire=evidence['request']
    if (result.get('outcome')!='operational' or result.get('reason')!='Verification unavailable'
        or result.get('contract_version')!=70 or result.get('contract_sha256')!=CONTRACT
        or result.get('candidate_revision')!=CANDIDATE or wire.get('request_id')!='v70-step9-verify'
        or wire.get('contract_version')!=70 or wire.get('contract_sha256')!=CONTRACT
        or wire.get('candidate_revision')!=CANDIDATE or evidence.get('gate')!='tests'
        or evidence.get('status')!='operational' or evidence.get('test_result') is not None
        or len(evidence.get('violations',[]))!=1 or evidence['violations'][0].get('message')!=DISCOVERY_ERROR
        or transaction.get('operation')!='v70-step9-verify' or transaction.get('stage')!='verify'
        or transaction.get('complete') is not True or submitted or compiled.get('request')!=wire
        or compiled.get('mode')!='compile' or compiled.get('status')!='completed'
        or compiled.get('passed') is not True or compiled.get('violations')):
        raise ValueError('Exact compiled cycle-70 zero-test-submission stop required')


def reconcile(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
              integration: Path,host: OverlayHost) -> bool:
    from operational_transport import retained_run_reservations
    from frozen_budget_continuation import check_frozen_sources
    from unity_coder.core.workspaces import git
    from unity_coder.core.storage import atomic_write
    run=state/'.agent/runs/monopoly-game-lobby'
    raw=(run/'services-v70/evidence/v70-step9-verify.json').read_bytes();evidence=json.loads(raw)
    if sha256(raw).hexdigest()!='a9d96d1f00aa706af2d4a7e79301c46a3730120dd084cc3fccaed09d2cbfffef':
        raise ValueError('Actual discovery-stop evidence changed')
    wire=evidence['request'];request=VerificationRequest(**(wire|{'test_selection':tuple(wire['test_selection'])}))
    folder=ticket_path(host.host,request)
    key=sha256(json.dumps({'request':wire,'mode':'compile'},sort_keys=True).encode()).hexdigest()
    compiled_raw=(host.host/'.agent/verification'/key/'result.json').read_bytes()
    if sha256(compiled_raw).hexdigest()!='97d1db9141c7c776a02feece22fb7c798faed5a002ccfe7ff00f3d2e84d76519':
        raise ValueError('Actual compiled callback changed')
    validate_stop(json.loads((run/'result.json').read_bytes()),evidence,services.effects.read('transaction'),
        json.loads(compiled_raw),submitted=(folder/'request.json').exists() or (folder/'result.json').exists())
    frozen=services.tdd._frozen_hashes;services.tdd.assert_frozen();check_frozen_sources(integration,frozen)
    preserved=json.loads((state/'context-optimization/preservation-v70.json').read_bytes())
    verify_preservation(preserved['budget'],budget._read(),preserved['frozen'],frozen)
    retained=retained_run_reservations(state,budget._read())
    if (len(retained)!=27 or len(frozen)!=199 or contract.sha256!=CONTRACT
        or git(integration,'rev-parse','HEAD').decode().strip()!=CANDIDATE or git(integration,'status','--porcelain')):
        raise ValueError('Current candidate, frozen inventory or reservations changed')
    for name,digest in {'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
        'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}.items():
        if sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:raise ValueError('Pinned overlay changed')
    overlay=host.overlay.read()
    if overlay['candidate']!=CANDIDATE or overlay['baseline_sha256']!='12f3b9e07d8085e8ad0558e02223988c7313ac4392f77d9c80a91d8c6e6d74a0':
        raise ValueError('Original overlay baseline changed')
    host.preflight();host.transport._discover_once();host.overlay.check(overlay)
    if (folder/'request.json').exists() or (folder/'result.json').exists():raise ValueError('Test intent appeared during recovery')
    atomic_write(state,'recovery-authorizations/v70-bridge-step9.json',json.dumps({
        'candidate':CANDIDATE,'contract_sha256':CONTRACT,'evidence_sha256':sha256(raw).hexdigest(),
        'compile_result_sha256':sha256(compiled_raw).hexdigest(),'zero_test_submission':True,
        'retained_uncertain':retained,'usage':budget.totals(),'test_ticket':folder.name,
        'new_native_operation_required':True,'human_accepted':False},indent=2).encode())
    return True
