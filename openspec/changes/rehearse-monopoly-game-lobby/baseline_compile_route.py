"""Target-host recovery of actual pre-freeze test compilation failures."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING
from unity_coder.core.dossiers import DossierUnit
from unity_coder.core.executor import StepResult
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

if TYPE_CHECKING:
    from unity_coder.core.ai_models import AIConfig
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.contracts import Contract
    from unity_coder.core.local_executor import LocalExecutionServices
    from lobby_production_host import ContextWorkers


def compile_authors(fact: dict, contract: Contract, candidate: str) -> tuple[str,...]:
    request=fact.get('request',{})
    if (fact.get('gate')!='compile' or fact.get('status')!='failed'
        or fact.get('test_result') is not None or not fact.get('violations')
        or request.get('candidate_revision')!=candidate or request.get('full_suite') is not True
        or request.get('contract_version')!=contract.contract_version
        or request.get('contract_sha256')!=contract.sha256
        or set(request.get('test_selection',[]))!={t.test_id for t in contract.test_links}):
        raise ValueError('Actual exact-candidate full baseline compile evidence required')
    authors=set();prefix='Assets/JJGame/monopoly/'
    for violation in fact['violations']:
        path=violation['file'].replace('\\','/')
        if not path.startswith(prefix) or violation.get('code')!='compile':
            raise ValueError('Compiler diagnostic outside the authorized module')
        relative=path[len(prefix):]
        owners=[u for u in contract.units if u.status=='active' and relative in u.owns]
        if len(owners)!=1 or owners[0].role!='test' or not relative.endswith('.cs'):
            raise ValueError('Compiler diagnostic is not uniquely owned unfrozen test source')
        authors.add(owners[0].id)
    return tuple(sorted(authors))


class CompileRouteServices:
    """ExecutionServices decorator using the existing legal red-to-prepare edge."""
    def __init__(self, inner: LocalExecutionServices, root: Path, route_key: str,
                 authors: tuple[str,...], feedback: str, guard: Callable[[],None]) -> None:
        self.inner,self.root,self.authors,self.feedback,self.guard=inner,root,authors,feedback,guard
        self.prefix='compile-routing/'+route_key

    def __getattr__(self, name: str) -> object:
        return getattr(self.inner,name)

    def _receipt(self) -> dict | None:
        path=self.root/self.prefix/'receipt.json'
        return json.loads(path.read_bytes()) if path.exists() else None

    def step(self, stage: str, operation_id: str) -> StepResult:
        receipt=self._receipt()
        if stage!='red' or (receipt and receipt['operation_id']!=operation_id):
            return self.inner.step(stage,operation_id)
        return self._route(operation_id)

    def reconcile(self, stage: str, operation_id: str) -> StepResult:
        receipt=self._receipt();intent=self.root/self.prefix/'intent.json'
        if stage=='red' and ((receipt and receipt['operation_id']==operation_id) or intent.exists()):
            return self._route(operation_id)
        return self.inner.reconcile(stage,operation_id)

    def _route(self, operation_id: str) -> StepResult:
        if self.inner.tdd.frozen:raise ValueError('Frozen tests cannot return to authoring')
        self.inner.preflight();self.guard()
        receipt=self._receipt()
        if receipt:
            if receipt['operation_id']!=operation_id:raise ValueError('Compile route operation changed')
            return StepResult(**receipt['report'])
        path=self.root/self.prefix/'intent.json'
        intent=json.loads(path.read_bytes()) if path.exists() else {
            'operation_id':operation_id,'authors':list(self.authors),
            'before':{u:self.inner.tdd.state(u).preparation_attempts for u in self.authors}}
        if intent['operation_id']!=operation_id or intent['authors']!=list(self.authors):
            raise ValueError('Compile route identity changed')
        if not path.exists():atomic_write(self.root,self.prefix+'/intent.json',json.dumps(intent).encode())
        exhausted=[]
        for author in self.authors:
            count=self.inner.tdd.state(author).preparation_attempts
            before=intent['before'][author]
            if count==before:
                try:self.inner.tdd.record_preparation_failure(author)
                except ValueError:
                    if self.inner.tdd.state(author).stage!='preparation_exhausted':raise
            elif count!=before+1:raise ValueError('Preparation attempt history changed')
            if self.inner.tdd.state(author).stage=='preparation_exhausted':exhausted.append(author)
        self.inner.state['feedback']=self.feedback
        self.inner._save()
        if exhausted:
            units={u.id:u for u in self.inner.contract.units}
            defects=tuple(DossierUnit(u,'contract',units[u].spec_ref,'compile',
                (self.inner.state['evidence_ref'],),self.feedback,
                self.inner.tdd.state(u).preparation_attempts,('preparation_exhausted',)) for u in exhausted)
            report=self.inner._contract_rework(defects,'Baseline compiler preparation allowance exhausted')
        else:report=StepResult('prepare',self.inner._statuses())
        atomic_write(self.root,self.prefix+'/receipt.json',json.dumps({
            'operation_id':operation_id,'report':asdict(report),'no_test_execution_claimed':True,
            'human_accepted':False},sort_keys=True).encode())
        return report


def arm(state: Path, contract: Contract, budget: BudgetLedger,
        services: LocalExecutionServices, integration: Path, workers: ContextWorkers,
        settings: AIConfig) -> CompileRouteServices:
    """Bind the recovery adapter to an actual durable compiler result, never a fabricated test outcome."""
    from operational_transport import retained_run_reservations
    run=state/'.agent/runs/monopoly-game-lobby'
    active_ref='compile-routing/active-v'+str(contract.contract_version)+'.json'
    active_path=state/active_ref
    driver=json.loads((run/('executor-v'+str(contract.contract_version)+'.json')).read_bytes())
    resumed=driver['stage']=='red' and active_path.exists()
    prior=json.loads(active_path.read_bytes()) if resumed else None
    if prior:
        result_raw=bytes.fromhex(prior['original_result_hex']);result=json.loads(result_raw)
        if (driver['pending'] not in (None,prior['next_operation'])
            or driver['steps'][-1]['result']!=result):
            raise ValueError('Compile route reconnect differs from the original native stop')
    else:
        result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    if (result.get('outcome')!='operational' or result.get('reason')!='No behavioral baseline available'
        or result.get('contract_version')!=contract.contract_version or services.tdd.frozen
        or settings.coder.model!='gpt-6.2-sol' or settings.judge.model!='gpt-6.1-sol'):
        raise ValueError('Only the actual unfrozen baseline compiler stop may arm recovery')
    refs=result['evidence_refs']
    if len(refs)!=1:raise ValueError('Unambiguous compiler evidence required')
    from unity_coder.core.ownership import confined_path
    evidence_path=confined_path(state,refs[0]);raw=evidence_path.read_bytes();fact=json.loads(raw)
    candidate=result['candidate_revision'];authors=compile_authors(fact,contract,candidate)
    retained_run_reservations(state,budget._read())
    key=sha256(raw+result_raw).hexdigest()
    if prior and prior['route_key']!=key:raise ValueError('Compile route fact identity changed')
    def guard() -> None:
        services.manager._assert_handle(services.integration,'integration')
        if (git(integration,'rev-parse','HEAD').decode().strip()!=candidate
            or git(integration,'status','--porcelain') or evidence_path.read_bytes()!=raw
            or services.tdd.frozen):
            raise ValueError('Compiler recovery candidate/evidence/freeze changed')
    guard()
    transaction=services.effects.read('transaction')
    if not transaction or not transaction['complete'] or transaction['stage']!='red':
        raise ValueError('Baseline verification effect must be complete')
    host=Path(os.environ['UNITY_HOST']).resolve(strict=True)
    sdk={}
    for name,first,last in (
        ('Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/IServiceBase.cs',0,60),
        ('Library/PackageCache/com.cysharp.unitask@2.5.11-jj.1/Runtime/UniTaskBreakableChain.cs',0,47),
        ('Library/PackageCache/com.cysharp.unitask@2.5.11-jj.1/Runtime/UniTaskBreakableChain.cs',138,170)):
        body=(host/name).read_bytes()
        sdk[name+':'+str(first+1)+'-'+str(last)]={'sha256':sha256(body).hexdigest(),
            'excerpt':'\n'.join(body.decode('utf-8-sig').splitlines()[first:last])}
    workers.supplemental_context={u:{'specs/monopoly-game-lobby/actual-compiler-sdk-context.json':json.dumps(sdk,ensure_ascii=False)} for u in authors}
    feedback='Baseline compiler preparation failure; repair only the owned recording fixture, preserve every effective assertion and all production files. Actual compiler diagnostics:\n'+'\n'.join(v['message'] for v in fact['violations'])
    atomic_write(state,'recovery-authorizations/compile-'+key+'.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':candidate,'evidence_ref':refs[0],
        'evidence_sha256':sha256(raw).hexdigest(),'previous_result_sha256':sha256(result_raw).hexdigest(),
        'authors':authors,'accounted_tokens':budget.totals(),'sdk_sources':sdk,
        'legal_transition':'red -> prepare','runtime_files_changed':False,'human_accepted':False},indent=2).encode())
    descriptor={'route_key':key,'original_result_hex':result_raw.hex(),
        'next_operation':f'v{contract.contract_version}-step{len(driver["steps"])+1}-red'}
    if prior:
        if prior!=descriptor:raise ValueError('Compile route descriptor changed')
    else:
        if active_path.exists() and json.loads(active_path.read_bytes())!=descriptor:
            raise ValueError('Existing compile route must be preserved and reconciled')
        if not active_path.exists():atomic_write(state,active_ref,json.dumps(descriptor,indent=2).encode())
    return CompileRouteServices(services,state,key,authors,feedback,guard)
