"""Target-only bounded readiness wait and exact pre-submission recovery."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import TYPE_CHECKING
from unity_coder.adapters.unity.transport import BridgeTransport
from unity_coder.core.verification import VerificationRequest,WorkerEvidence
if TYPE_CHECKING:
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.contracts import Contract
    from unity_coder.core.local_executor import LocalExecutionServices
    from overlay_host import OverlayHost

DISCOVERY_ERROR='No exact-project Bridge with FrameworkVerify tooling'
CONTRACT='e4db83d9eed559a43be0a4b3c1626494b90e8d4322097510d144ef2ae53d9b9e'
CANDIDATE='73816996becb75eb390b0625f69c67ca630774f7'


def ticket_path(root: Path,request: VerificationRequest) -> Path:
    raw=json.dumps({'request':asdict(request),'mode':'tests'},sort_keys=True).encode()
    return root/'.agent/verification'/sha256(raw).hexdigest()


class ReadinessWaitTransport:
    def __init__(self,inner: BridgeTransport,*,ready: Callable[[],None],record: Callable[[dict],None],
                 pause: Callable[[float],None]=time.sleep) -> None:
        self.inner,self.ready,self.record,self.pause=inner,ready,record,pause

    def compile(self,request: VerificationRequest) -> WorkerEvidence:
        return self.inner.compile(request)

    def _eligible(self,request: VerificationRequest,evidence: WorkerEvidence) -> bool:
        folder=ticket_path(self.inner.root,request)
        return (evidence.request==request and evidence.tests is not None
            and evidence.tests.operational_error==DISCOVERY_ERROR
            and not (folder/'request.json').exists() and not (folder/'result.json').exists())

    def run_tests(self,request: VerificationRequest) -> WorkerEvidence:
        evidence=self.inner.run_tests(request)
        for attempt in range(1,4):
            if not self._eligible(request,evidence):return evidence
            try:self.ready()
            except (OSError,ValueError):
                if attempt<3:self.pause(1)
                continue
            if not self._eligible(request,evidence):return evidence
            self.record({'request':asdict(request),'test_ticket':ticket_path(self.inner.root,request).name,
                'reason':DISCOVERY_ERROR,'zero_submission':True,'readiness_attempt':attempt,'bounded_retries':3})
            evidence=self.inner.run_tests(request)
            if not self._eligible(request,evidence):return evidence
            if attempt<3:self.pause(1)
        return evidence


def validate_stop(result: dict,evidence: dict,transaction: dict,compiled: dict,*,submitted: bool) -> None:
    wire=evidence['request']
    if (result.get('outcome')!='operational' or result.get('contract_version')!=69
        or result.get('contract_sha256')!=CONTRACT or result.get('candidate_revision')!=CANDIDATE
        or wire.get('request_id')!='v69-step9-verify' or wire.get('contract_version')!=69
        or wire.get('contract_sha256')!=CONTRACT or wire.get('candidate_revision')!=CANDIDATE
        or evidence.get('gate')!='tests' or evidence.get('status')!='operational'
        or evidence.get('test_result') is not None or len(evidence.get('violations',[]))!=1
        or evidence['violations'][0].get('message')!=DISCOVERY_ERROR
        or transaction.get('operation')!='v69-step9-verify' or transaction.get('stage')!='verify'
        or transaction.get('complete') is not True or submitted
        or compiled.get('request')!=wire or compiled.get('mode')!='compile'
        or compiled.get('status')!='completed' or compiled.get('passed') is not True
        or compiled.get('violations')):
        raise ValueError('Exact compiled cycle-69 zero-submission operational stop required')


def reconcile(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
              integration: Path,host: OverlayHost) -> bool:
    from frozen_budget_continuation import check_frozen_sources
    from operational_transport import retained_run_reservations
    from unity_coder.core.storage import atomic_write
    from unity_coder.core.workspaces import git
    run=state/'.agent/runs/monopoly-game-lobby'
    raw=(run/'services-v69/evidence/v69-step9-verify.json').read_bytes();evidence=json.loads(raw)
    if sha256(raw).hexdigest()!='296c78e5eec9038e79764cc17984a1b6b7390f247d7aa3c1d8fe3dca027bbe2c':
        raise ValueError('Actual native operational evidence changed')
    result=json.loads((run/'result.json').read_bytes());wire=evidence['request']
    request=VerificationRequest(**(wire|{'test_selection':tuple(wire['test_selection'])}))
    folder=ticket_path(host.host,request)
    compile_key=sha256(json.dumps({'request':wire,'mode':'compile'},sort_keys=True).encode()).hexdigest()
    compiled_raw=(host.host/'.agent/verification'/compile_key/'result.json').read_bytes()
    compiled=json.loads(compiled_raw)
    validate_stop(result,evidence,services.effects.read('transaction'),compiled,
        submitted=(folder/'request.json').exists() or (folder/'result.json').exists())
    frozen=json.loads((state/services.prefix/'state.json').read_bytes())['tdd']['frozen']
    if (contract.sha256!=CONTRACT or budget.limits!=[250000000,24000000,160,2]
        or git(integration,'rev-parse','HEAD').decode().strip()!=CANDIDATE
        or git(integration,'status','--porcelain') or not services.tdd.frozen
        or len(frozen)!=199 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!=
        '2da65db6815d61fb277a19f826b4d512e78c8bc4dc2f4f8c4d1b3387e8d1c520'):
        raise ValueError('Frozen candidate or persistent limits changed')
    services.tdd.assert_frozen();check_frozen_sources(integration,frozen)
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=25:raise ValueError('Every historical uncertain reservation must remain')
    pinned={'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
        'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}
    for name,digest in pinned.items():
        if sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:raise ValueError('Pinned overlay changed')
    overlay=host.overlay.read()
    if overlay['candidate']!=CANDIDATE or overlay['baseline_sha256']!='12f3b9e07d8085e8ad0558e02223988c7313ac4392f77d9c80a91d8c6e6d74a0':
        raise ValueError('Dedicated host overlay identity changed')
    host.preflight()
    if (folder/'request.json').exists() or (folder/'result.json').exists():raise ValueError('A test intent appeared; stop recovery')
    atomic_write(state,'recovery-authorizations/v69-bridge-step9-resume.json',json.dumps({
        'candidate':CANDIDATE,'contract_sha256':CONTRACT,'operational_evidence_sha256':sha256(raw).hexdigest(),
        'compile_result_sha256':sha256(compiled_raw).hexdigest(),'zero_test_submission':True,
        'test_ticket':folder.name,'frozen_count':199,'retained_uncertain':retained,'usage':budget.totals(),
        'human_accepted':False},indent=2).encode())
    return True
