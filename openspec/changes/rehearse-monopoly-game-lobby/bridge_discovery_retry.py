"""Target-only retry for discovery that provably preceded any test submission."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from collections.abc import Callable
from typing import TYPE_CHECKING
from unity_coder.adapters.unity.transport import BridgeTransport
from unity_coder.core.verification import VerificationRequest,WorkerEvidence
if TYPE_CHECKING:
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.contracts import Contract
    from unity_coder.core.local_executor import LocalExecutionServices
    from overlay_host import OverlayHost

DISCOVERY_ERROR='No exact-project Bridge with FrameworkVerify tooling'


def ticket_path(root: Path, request: VerificationRequest) -> Path:
    raw=json.dumps({'request':asdict(request),'mode':'tests'},sort_keys=True).encode()
    return root/'.agent/verification'/sha256(raw).hexdigest()


class DiscoveryRetryTransport:
    def __init__(self, inner: BridgeTransport, *, ready: Callable[[],None], record: Callable[[dict],None]) -> None:
        self.inner,self.ready,self.record=inner,ready,record

    def compile(self, request: VerificationRequest) -> WorkerEvidence:
        return self.inner.compile(request)

    def run_tests(self, request: VerificationRequest) -> WorkerEvidence:
        evidence=self.inner.run_tests(request)
        folder=ticket_path(self.inner.root,request)
        if (evidence.request!=request or evidence.tests is None
            or evidence.tests.operational_error!=DISCOVERY_ERROR
            or (folder/'request.json').exists() or (folder/'result.json').exists()):return evidence
        try:self.ready()
        except (OSError,ValueError):return evidence
        # Recheck after readiness; an intent appearing meanwhile forbids retry.
        if (folder/'request.json').exists() or (folder/'result.json').exists():return evidence
        self.record({'request':asdict(request),'test_ticket':folder.name,
            'reason':DISCOVERY_ERROR,'zero_submission':True,'bounded_retry':1})
        return self.inner.run_tests(request)


def reconcile_red_discovery(state: Path,contract: Contract,budget: BudgetLedger,
                            services: LocalExecutionServices,integration: Path,host: OverlayHost) -> bool:
    from frozen_budget_continuation import check_frozen_sources
    from operational_transport import retained_run_reservations
    from unity_coder.core.storage import atomic_write
    from unity_coder.core.workspaces import git
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    raw=(run/'services-v64/evidence/v64-step2-red.json').read_bytes();evidence=json.loads(raw)
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=64 or contract.sha256!='3736a09ad5d104d5da479ae114e3f8735070999d86a2472f1497efbccb933151'
        or result['outcome']!='operational' or result['candidate_revision']!='02460607473eb7be1cb5919f3daa1de160c92d0d'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or evidence['status']!='operational' or evidence['gate']!='tests'
        or evidence['test_result'] is not None or len(evidence['violations'])!=1
        or evidence['violations'][0]['message']!=DISCOVERY_ERROR
        or transaction['operation']!='v64-step2-red' or not transaction['complete']):
        raise ValueError('Exact pre-submission discovery stop identity changed')
    wire=evidence['request'];request=VerificationRequest(**(wire|{'test_selection':tuple(wire['test_selection'])}))
    folder=ticket_path(host.host,request)
    if (folder/'request.json').exists() or (folder/'result.json').exists():
        raise ValueError('A test submission exists; no pre-submission recovery')
    compile_key=sha256(json.dumps({'request':wire,'mode':'compile'},sort_keys=True).encode()).hexdigest()
    compiled=json.loads((host.host/'.agent/verification'/compile_key/'result.json').read_bytes())
    if (compiled['request']!=wire or compiled['mode']!='compile' or compiled['status']!='completed'
        or compiled['passed'] is not True or compiled.get('violations')):
        raise ValueError('Matching actual compilation evidence required')
    manifest=json.loads((state/'frozen-continuations/v64.json').read_bytes())
    check_frozen_sources(integration,manifest['frozen'])
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=23:raise ValueError('Unknown reservations changed')
    host.preflight()
    atomic_write(state,'recovery-authorizations/v64-bridge-discovery-resume.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'operational_evidence_sha256':sha256(raw).hexdigest(),'test_ticket':folder.name,
        'zero_test_submission':True,'compile_passed':True,'frozen_count':len(manifest['frozen']),
        'retained_uncertain':retained,'usage':budget.totals(),'human_accepted':False},indent=2).encode())
    return True
