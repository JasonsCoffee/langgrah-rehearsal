"""Respect a real negative review without attempting to edit frozen test files."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from collections.abc import Callable
from typing import TYPE_CHECKING
from unity_coder.core.dossiers import DossierUnit
from unity_coder.core.executor import StepResult
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
if TYPE_CHECKING:
    from unity_coder.core.contracts import Contract
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.local_executor import LocalExecutionServices


def frozen_defect(owns: tuple[str,...], frozen: dict[str,str], decision: dict, attempts: int) -> dict:
    if (decision.get('valid') is not False or not isinstance(decision.get('explanation'),str)
        or not decision['explanation'].strip() or not owns or not set(owns)<=set(frozen)
        or type(attempts) is not int or attempts<1):
        raise ValueError('Actual rejected review and completely frozen scope required')
    return {'reason':decision['explanation'],'attempts':attempts}


class FrozenReviewServices:
    def __init__(self, inner: LocalExecutionServices, state: Path, proof: dict, guard: Callable[[],None]) -> None:
        self.inner,self.root,self.proof,self.guard=inner,state,proof,guard
        self.prefix='frozen-review-routing/v65'

    def __getattr__(self,name: str) -> object:return getattr(self.inner,name)

    def step(self,stage: str,operation_id: str) -> StepResult:
        if stage!='prepare':return self.inner.step(stage,operation_id)
        return self._route(operation_id)

    def reconcile(self,stage: str,operation_id: str) -> StepResult:
        if stage=='prepare':return self._route(operation_id)
        return self.inner.reconcile(stage,operation_id)

    def _route(self,operation_id: str) -> StepResult:
        self.guard();self.inner.preflight()
        path=self.root/self.prefix/'receipt.json'
        if path.exists():
            value=json.loads(path.read_bytes())
            if value['operation_id']!=operation_id:raise ValueError('Frozen review route operation changed')
            return StepResult(**value['report'])
        atomic_write(self.root,self.prefix+'/intent.json',json.dumps({'operation_id':operation_id,'proof':self.proof},sort_keys=True).encode())
        unit=next(u for u in self.inner.contract.units if u.id==self.proof['unit_id'])
        finding=DossierUnit(unit.id,'contract',unit.spec_ref,'tests',tuple(self.proof['evidence_refs']),
            self.proof['reason']+' Existing owned files are already frozen. Add supplementary coverage in new owned files; preserve every old assertion and byte.',
            self.proof['attempts'],('actual_frozen_source_review_rejection',))
        report=self.inner._contract_rework((finding,),'Actual independent coverage rejection requires new test ownership; existing tests remain frozen')
        self.inner._save()
        atomic_write(self.root,self.prefix+'/receipt.json',json.dumps({'operation_id':operation_id,'report':asdict(report),
            'counter_incremented':False,'test_files_changed':False,'human_accepted':False},sort_keys=True).encode())
        return report


def arm(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
        integration: Path) -> FrozenReviewServices:
    from frozen_budget_continuation import check_frozen_sources
    from operational_transport import retained_run_reservations
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    call='v65-step1-prepare-review-TEST-PARTNER-RECS';key=sha256(call.encode()).hexdigest()
    receipt_ref='.agent/runs/monopoly-game-lobby/model-calls/'+key+'.json'
    raw=(state/receipt_ref).read_bytes();receipt=json.loads(raw);decision=json.loads(receipt['reply']['text'])
    sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes());charge=budget._read()['calls'][call]
    unit=next(u for u in contract.units if u.id=='TEST-PARTNER-RECS')
    manifest=json.loads((state/'frozen-continuations/v65.json').read_bytes());frozen=manifest['frozen']
    finding=frozen_defect(unit.owns,frozen,decision,services.tdd.state(unit.id).preparation_attempts)
    tx=services.effects.read('transaction')
    if (contract.contract_version!=65 or contract.sha256!='edddecafb90f10bfab23e7aadeac2640bf57582a3e04c1e5e376975305b54e5b'
        or result['outcome']!='operational' or result['candidate_revision']!='36cdcd196d5024844066814f81c429fabc4ac898'
        or tx['operation']!='v65-step2-prepare' or not tx['complete'] or services.tdd.frozen
        or finding['attempts']!=1 or receipt['reply']['model']!='gpt-6.1-sol'
        or receipt['identity']['effort']!='medium' or sdk['text']!=receipt['reply']['text']
        or charge.get('actual')!=[sdk['input_tokens'],sdk['output_tokens']]
        or sdk['policy_sha256']!=receipt['identity']['backend_policy_sha256']):
        raise ValueError('Exact actual frozen-review stop required')
    rejected_ref='.agent/runs/monopoly-game-lobby/services-v65/evidence/v65-step1-prepare-review-TEST-PARTNER-RECS.json'
    rejected=(state/rejected_ref).read_bytes()
    if decision['explanation'] not in json.loads(rejected)['reason']:raise ValueError('Native rejection evidence changed')
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=23:raise ValueError('Uncertain reservations changed')
    def guard() -> None:
        if git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain'):
            raise ValueError('Frozen-review candidate changed')
        if (state/receipt_ref).read_bytes()!=raw or (state/rejected_ref).read_bytes()!=rejected:
            raise ValueError('Actual negative review changed')
        check_frozen_sources(integration,frozen)
        if services.tdd.state(unit.id).preparation_attempts!=1:raise ValueError('Actual attempt count changed')
    guard()
    proof={'unit_id':unit.id,**finding,'receipt_sha256':sha256(raw).hexdigest(),
        'evidence_refs':[receipt_ref,rejected_ref],'retained_uncertain':retained,'usage':budget.totals(),
        'frozen_count':len(frozen),'human_accepted':False}
    atomic_write(state,'recovery-authorizations/frozen-review-v65.json',json.dumps(proof,indent=2).encode())
    return FrozenReviewServices(services,state,proof,guard)
