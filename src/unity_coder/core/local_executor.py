"""Local composition: isolated coding, sequential verification, bounded repairs."""

from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Protocol

from .budget import BudgetLedger, BudgetExhausted
from .ai_models import ModelError
from .governor import BudgetGovernor
from .completion import CandidateCompletion
from .constraints import LearnedConstraint, accepted_constraints
from .contracts import Unit, _object, _ref, _items
from .dispatch import ready_units
from .dossiers import DossierUnit, emit_dossier
from .evidence import TestResult, Violation
from .execution_host import ExecutionHost
from .effects import DurableEffects
from .integration import invalidate_dependents
from .executor import StepResult
from .loop_control import Attempt, Observation, RetryPolicy, RetryState
from .ownership import confined_path
from .review import ReviewGate, ReviewPackage
from .storage import atomic_write, file_guard
from .tdd import BehaviorEvidence, TDDCoordinator, UnitTDD, validate_behavior
from .verification import VerificationRequest, VerificationResult
from .workspaces import Workspace, WorkspaceCandidate, WorkspaceManager, git


@dataclass(frozen=True)
class WorkerPatch:
    files: Mapping[str, bytes]
    reason: str


class TestReviewRejected(ValueError):
    """Independent preparation feedback; not a provider transport failure."""
    __test__ = False


class ExecutionCancelled(Exception):
    """Stop new effects after active synchronous workers have reconciled."""


class CodingWorkers(Protocol):
    def code(self, unit: Unit, stage: str, files: Mapping[str, str], feedback: str, operation_id: str) -> WorkerPatch: ...
    def review_tests(self, unit: Unit, files: Mapping[str, str], operation_id: str) -> str: ...
    def judge(self, unit: Unit, evidence: VerificationResult, files: Mapping[str, str], operation_id: str) -> tuple[str, str]: ...


Verifier = Callable[[VerificationRequest, Path, Mapping[str, Mapping[str, bytes | None]]], VerificationResult]


def _tests(raw: dict) -> TestResult:
    return TestResult(**{key: tuple(value) if isinstance(value, list) else value for key, value in raw.items()})


def _verification(raw: dict) -> VerificationResult:
    request = dict(raw["request"])
    request["test_selection"] = tuple(request["test_selection"])
    return VerificationResult(VerificationRequest(**request), raw["gate"], raw["status"],
        tuple(raw["related_units"]), tuple(Violation(**v) for v in raw["violations"]),
        tuple(raw["failed_tests"]), _tests(raw["test_result"]) if raw["test_result"] else None,
        raw["full_suite_verified"], raw["behavioral"])


class LocalExecutionServices:
    def __init__(self, manager: WorkspaceManager, integration: Workspace, budget: BudgetLedger,
                 workers: CodingWorkers, verify: Verifier, review: ReviewGate, *,
                 preflight: Callable[[], None], test_config_paths: tuple[str, ...] = (),
                 max_attempts: int = 3,
                 review_package: Callable[[VerificationRequest], ReviewPackage] | None = None) -> None:
        self.manager, self.integration, self.budget = manager, integration, budget
        self.workers, self.verifier, self.review, self.preflight = workers, verify, review, preflight
        self.contract, self.root = manager.contract, budget.root
        self.review_package = review_package or self._default_review_package
        self.prefix = review.lifecycle.prefix + f"/services-v{self.contract.contract_version}"
        if (review.lifecycle.run_id != manager.run_id or review.lifecycle.contract_sha256 != self.contract.sha256
            or review.root.resolve() != budget.root.resolve() or budget.path != review.lifecycle.prefix + "/budget.json"):
            raise ValueError("Local service resource identity mismatch")
        self.tdd = TDDCoordinator(self.contract, integration.path, manager.rules,
                                  test_config_paths=test_config_paths, protected_paths=manager.frozen_paths)
        self.retry = RetryPolicy(max_attempts=max_attempts)
        self.state: dict = {"group":[], "patches":{}, "snapshots":{}, "verification":None, "feedback":""}
        self.active_verification: str | None = None
        self.activity: dict[str,str] = {}
        self.effects = DurableEffects(self.root,self.prefix+'/effects',manager,integration)
        saved = confined_path(self.root, self.prefix + "/state.json")
        if saved.exists():
            self._restore(json.loads(saved.read_bytes()))

    def _files(self) -> dict[str, bytes]:
        revision = git(self.integration.path,"rev-parse","HEAD").decode().strip()
        paths = git(self.integration.path,"ls-tree","-r","--name-only","-z",revision).decode().split("\0")
        return {p:confined_path(self.integration.path,p).read_bytes() for p in paths if p}

    def _context(self) -> dict[str, str]:
        paths = {p for u in self.contract.units if u.status == "active" for p in u.owns}
        paths.add(self.contract.spec.path)
        profile = self.contract.coding_profile_ref
        raw = confined_path(self.integration.path, profile.path).read_bytes()
        if sha256(raw).hexdigest() != profile.sha256:
            raise ValueError("Coding profile hash changed before dispatch")
        policy = _object(json.loads(raw))
        paths.add(profile.path)
        for reference in _items(policy.get("rules", [])):
            paths.add(_ref(reference, self.integration.path).path)
        return {p:confined_path(self.integration.path,p).read_text(encoding="utf-8")
                for p in sorted(paths) if confined_path(self.integration.path,p).is_file()}

    def _save(self) -> dict:
        payload = {"contract_sha256":self.contract.sha256, "state":self.state,
                   "candidate_revision":git(self.integration.path,"rev-parse","HEAD").decode().strip(),
                   "tdd": {"states":{u:asdict(s) for u,s in self.tdd._states.items()},
                           "reviews":self.tdd._reviews,"frozen":self.tdd._frozen_hashes,
                           "baseline_hashes":self.tdd._baseline_test_hashes,
                           "green":{u:{p:v.hex() if v is not None else None for p,v in files.items()}
                                    for u,files in self.tdd._green_files.items()}},
                   "retry":{u:asdict(self.retry.state(u)) for u in self.tdd.units}}
        atomic_write(self.root,self.prefix + "/state.json",json.dumps(payload,sort_keys=True).encode())
        return payload

    def _restore(self, payload: dict) -> None:
        if payload["contract_sha256"] != self.contract.sha256:
            raise ValueError("Local executor checkpoint contract changed")
        if payload.get("candidate_revision") != git(self.integration.path,"rev-parse","HEAD").decode().strip():
            transaction=self.effects.read('transaction')
            head=git(self.integration.path,'rev-parse','HEAD').decode().strip()
            completion_recovered = False
            if transaction and not transaction.get('complete') and transaction['stage'] == 'finalize':
                evidence = _verification(transaction['checkpoint']['state']['verification'])
                completion = CandidateCompletion(self.manager,self.integration,self.review)
                intent_path = confined_path(self.root,completion.path)
                if intent_path.exists():
                    intent = json.loads(intent_path.read_bytes())
                    if intent['before'] == payload['candidate_revision'] and intent['after'] == head:
                        self._complete(evidence.request)
                        completion_recovered = True
            if (not transaction or transaction.get('complete') or
                not (completion_recovered or self.effects.reconciles(payload['candidate_revision'],head))):
                raise ValueError("Checkpoint candidate changed; reconcile external effects")
        self.state = payload["state"]
        saved = payload["tdd"]
        states = {}
        for unit, raw in saved["states"].items():
            raw = dict(raw)
            baseline = raw["baseline"]
            if baseline:
                raw["baseline"] = BehaviorEvidence(baseline["snapshot"],tuple(baseline["requested"]),
                                                   _tests(baseline["result"]),baseline["failure_kind"])
            states[unit] = UnitTDD(**raw)
        if set(states) != set(self.tdd.units):
            raise ValueError("Checkpoint unit membership changed")
        self.tdd._states, self.tdd._reviews = states, saved["reviews"]
        self.tdd._frozen_hashes, self.tdd._baseline_test_hashes = saved["frozen"], saved["baseline_hashes"]
        self.tdd._green_files = {u:{p:bytes.fromhex(v) if v is not None else None for p,v in files.items()}
                                for u,files in saved["green"].items()}
        def observation(raw):
            return Observation(**(raw | {"failing":tuple(raw["failing"]), "selection":tuple(raw["selection"])})) if raw else None
        retries = {}
        for unit, raw in payload["retry"].items():
            retries[unit] = RetryState(raw["failed_attempts"],raw["regressions"],observation(raw["previous"]),
                tuple(Attempt(a["stage"],a["trend"],observation(a["observation"])) for a in raw["history"]),raw["escalated"])
        self.retry = RetryPolicy(max_attempts=self.retry.max_attempts,states=retries)
        if self.tdd.frozen:
            self.tdd.assert_frozen()

    def _statuses(self) -> dict[str,str]:
        return {u:self.tdd.state(u).stage for u in self.tdd.units}

    def _default_review_package(self, request: VerificationRequest) -> ReviewPackage:
        reference = self.contract.presentation_ref
        raw = confined_path(self.integration.path,reference.path).read_bytes()
        if sha256(raw).hexdigest() != reference.sha256:
            raise ValueError('Presentation changed before human review')
        manifest = _object(json.loads(raw))
        if manifest:
            # Visual targets require Architect-authored interaction instructions;
            # serialized mutations alone do not describe how a human reviews UX.
            instructions = manifest.get('instructions','')
            entries = tuple(manifest.get('entries',()))
            references = tuple(dict.fromkeys(asset['reference'] for asset in manifest.get('assets',())))
            return ReviewPackage(request,'visual',entries,instructions,(instructions,),references,
                'Review behavior and layout against the references; placeholder artwork is not final-art polish.')
        # Empty presentation is an explicit code-only contract, used by headless fixtures.
        return ReviewPackage(request,'code',(self.contract.spec.path,),
            'Inspect the candidate source and specification alongside its recorded verification evidence.',
            tuple(link.criterion for link in self.contract.test_links),(),
            'No visual presentation is declared; this review does not accept visual artwork or layout.')

    def confirm_constraints(self, request: VerificationRequest, entries: tuple[LearnedConstraint, ...]) -> None:
        """Trusted host input after human approval, before resuming finalization."""
        completion = CandidateCompletion(self.manager,self.integration,self.review)
        with file_guard(self.root,self.prefix+'/constraints.guard'), file_guard(self.root,completion.guard):
            if self.review.state().get('request') != json.loads(json.dumps(asdict(request))):
                raise ValueError('Constraint confirmation belongs to another review')
            original = completion._files(request.candidate_revision).get('AGENTS.md',b'')
            accepted_constraints(self.review,candidate_revision=request.candidate_revision,
                contract_version=request.contract_version,original=original,entries=entries)
            record = {'request':asdict(request),'entries':[asdict(entry) for entry in entries]}
            content = json.dumps(record,sort_keys=True).encode()
            path = self.prefix+'/confirmed-constraints.json'
            existing = confined_path(self.root,path)
            if existing.exists():
                if existing.read_bytes() != content:
                    raise ValueError('Confirmed constraints are immutable')
                return
            if confined_path(self.root,completion.path).exists():
                raise ValueError('Completion already started')
            atomic_write(self.root,path,content)

    def _completion_entries(self, request: VerificationRequest) -> tuple[LearnedConstraint, ...]:
        path = confined_path(self.root,self.prefix+'/confirmed-constraints.json')
        if not path.exists():
            return ()
        record = json.loads(path.read_bytes())
        if record['request'] != json.loads(json.dumps(asdict(request))):
            raise ValueError('Confirmed constraint candidate changed')
        return tuple(LearnedConstraint(**entry) for entry in record['entries'])

    def _complete(self, request: VerificationRequest) -> dict[str, object]:
        # Serialize selection of confirmed entries with confirmation itself, not
        # just the later Git publication, so a successful confirmation cannot be lost.
        with file_guard(self.root,self.prefix+'/constraints.guard'):
            return CandidateCompletion(self.manager,self.integration,self.review).complete(
                request,self._completion_entries(request))

    def progress_snapshot(self) -> tuple[dict[str,str], dict[str,int], str | None]:
        return (self._statuses() | self.activity,{u:self.retry.state(u).failed_attempts + self.tdd.state(u).preparation_attempts
                                 for u in self.tdd.units},self.active_verification)

    def _check_cancel(self) -> None:
        path = confined_path(self.root,self.review.lifecycle.prefix + "/cancel.json")
        if path.exists():
            record = json.loads(path.read_bytes())
            if record.get("requested") is True:
                if record.get("contract_sha256",self.contract.sha256) != self.contract.sha256:
                    raise ValueError("Cancellation belongs to another contract")
                raise ExecutionCancelled()

    def reconcile(self, stage: str, operation_id: str) -> StepResult:
        path = confined_path(self.root,self.prefix + "/receipts/" + operation_id + ".json")
        if not path.exists():
            transaction=self.effects.read('transaction')
            if not transaction or transaction['stage']!=stage or transaction['operation']!=operation_id:
                raise ValueError("Pending effects require host reconciliation; no automatic replay")
            self._restore(transaction['checkpoint'])
            return self.step(stage,operation_id)
        receipt = json.loads(path.read_bytes())
        if receipt["stage"] != stage:
            raise ValueError("Service receipt stage changed")
        self._restore(receipt["checkpoint"])
        report = receipt["report"]
        return StepResult(report["next_stage"],report["units"],report["result"])

    def step(self, stage: str, operation_id: str) -> StepResult:
        self.preflight()
        self.manager._assert_handle(self.integration,"integration")
        if git(self.integration.path,"status","--porcelain"):
            raise ValueError("Dirty integration candidate requires reconciliation")
        if self.tdd.frozen:
            self.tdd.assert_frozen()
        transaction=self.effects.read('transaction')
        if not transaction or transaction['operation']!=operation_id:
            self.effects.write('transaction',{'stage':stage,'operation':operation_id,'checkpoint':self._save(),'complete':False})
        try:
            self._check_cancel()
            report = self._step(stage,operation_id)
            self._check_cancel()
        except ExecutionCancelled:
            report = self._end("cancelled","Explicit cancellation; active workers reconciled",
                               (self.state["evidence_ref"],) if self.state.get("evidence_ref") else ())
        except BudgetExhausted as exc:
            # ThreadPoolExecutor's context has joined all coding callbacks before
            # this catch; already admitted candidates remain journaled for the governor.
            result = BudgetGovernor(self.manager,self.integration,self.budget).abandon(
                reconcile_workers=lambda:True,input_tokens=exc.input_tokens,output_tokens=exc.output_tokens)
            report = StepResult("ended",self._statuses(),result)
        except ModelError:
            try:self._check_cancel()
            except ExecutionCancelled:
                report = self._end('cancelled','Explicit cancellation; uncertain worker receipts retained',())
            else:
                report = self._end("operational","Model transport requires reconciliation",())
        except Exception:
            try:self._check_cancel()
            except ExecutionCancelled:
                report=self._end('cancelled','Explicit cancellation; workers reconciled',())
            else:raise
        finally:
            self.activity.clear()
        checkpoint = self._save()
        atomic_write(self.root,self.prefix + "/receipts/" + operation_id + ".json",
                     json.dumps({"stage":stage,"report":asdict(report),"checkpoint":checkpoint},sort_keys=True).encode())
        transaction=self.effects.read('transaction')
        self.effects.write('transaction',dict(transaction,complete=True))
        return report

    def _code(self, group: tuple[str,...], stage: str, operation: str) -> None:
        if not group:
            raise ValueError("No schedulable coding units")
        plan=self.effects.read('code-'+operation)
        if plan is None:
            plan={'base':git(self.integration.path,"rev-parse","HEAD").decode().strip(),
                  'group':list(group),'stage':stage,'context':self._context(),'feedback':self.state['feedback'],
                  'snapshots':{u:{p:confined_path(self.integration.path,p).read_bytes().hex()
                                 if confined_path(self.integration.path,p).is_file() else None
                                 for p in self.tdd.units[u].owns} for u in group}}
            self.effects.write('code-'+operation,plan)
        if plan['group']!=list(group) or plan['stage']!=stage:raise ValueError('Coding plan changed')
        base = plan['base']
        frozen = tuple(self.tdd._frozen_hashes or {}) + self.manager.frozen_paths
        isolated = WorkspaceManager(self.manager.repository,self.manager.workspace_root,self.contract,self.manager.rules,
                                    run_id=self.manager.run_id + "-" + operation,imported_roots=(),frozen_paths=frozen)
        handles = {}
        context = plan['context']
        for unit_id in group:
            unit = self.tdd.units[unit_id]
            dependencies = {d:self.contract.sha256 if self.tdd.units[d].interfaces else base for d in unit.depends_on}
            path=isolated.workspace_root/isolated.run_id/f'unit-v{self.contract.contract_version}-{unit_id}'
            handles[unit_id] = (isolated.reopen_unit(unit_id,base,dependencies) if path.exists()
                                else isolated.create_unit(unit_id,base,dependencies))
            self.state["snapshots"][unit_id] = plan['snapshots'][unit_id]
        def generate(unit_id: str):
            unit = self.tdd.units[unit_id]
            self._check_cancel()
            self.activity[unit_id]=stage+'_coding'
            def invoke() -> dict:
                patch=self.workers.code(unit,stage,context,plan['feedback'],operation+'-'+unit_id)
                return {'files':{p:v.hex() for p,v in patch.files.items()},'reason':patch.reason}
            saved=self.effects.call('worker-'+operation+'-'+unit_id,{'stage':stage,'unit':unit_id,'base':base},invoke)
            patch=WorkerPatch({p:bytes.fromhex(v) for p,v in saved['files'].items()},saved['reason'])
            self.tdd.validate_patch(unit_id,patch.files)
            if not patch.reason.strip():
                raise ValueError("Worker patch requires rationale")
            host = ExecutionHost(handles[unit_id],self.contract,self.manager.rules,frozen_paths=frozen)
            for path, content in patch.files.items():
                host.write_file(path,content)
            result=isolated.capture(handles[unit_id]), patch.reason
            self.activity[unit_id]='awaiting_verification'
            return result
        self.state["patches"] = {}
        admitted: set[str] = set()
        with ThreadPoolExecutor(max_workers=len(group),thread_name_prefix="coding-unit") as pool:
            futures = [pool.submit(generate,unit_id) for unit_id in group]
            for future in as_completed(futures):
                candidate,reason = future.result()
                self._check_cancel()
                self.effects.apply(operation+'-'+candidate.unit_id,candidate)
                admitted.add(candidate.unit_id)
                self.state["patches"][candidate.unit_id] = {p:v.hex() if v is not None else None for p,v in candidate.changes.items()}
                if stage == "refactor" and not candidate.changes:
                    self.tdd.finish_refactor(candidate.unit_id,reason=reason)
                elif stage == "refactor":
                    self.tdd.begin_refactor(candidate.unit_id)
                # Early focused evidence is provisional: final integrated evidence
                # still governs Green/Refactor and review. No peer can change the
                # coordinator snapshot while this blocking verifier call runs.
                if stage == 'green' and any(not f.done() for f in futures):
                    eligible = tuple(u for u in sorted(admitted) if all(
                        set(link.implementing_units) <= admitted for link in self.contract.test_links
                        if u in link.implementing_units))
                    if eligible:
                        previous=self.state['group']
                        self.state['group']=list(eligible)
                        try:
                            early=self._verify(operation+'-early-'+candidate.unit_id,full=False)
                            if early.status=='operational':raise ModelError('Early verification requires reconciliation')
                        finally:self.state['group']=previous

    def _verify(self, operation: str, *, full: bool) -> VerificationResult:
        selection = tuple(link.test_id for link in self.contract.test_links) if full else tuple(dict.fromkeys(
            test for unit in self.state["group"] for test in self.tdd.units[unit].acceptance))
        revision = git(self.integration.path,"rev-parse","HEAD").decode().strip()
        request = VerificationRequest(operation,self.manager.run_id,self.contract.contract_version,self.contract.sha256,
            revision,self.contract.presentation_ref.sha256,self.contract.coding_profile_ref.sha256,
            self.contract.environment_ref.sha256,selection,full)
        previous = self.effects.read('verify-'+operation)
        if previous and 'result' in previous:
            verified_revision = previous['identity']['request']['candidate_revision']
            if verified_revision != revision:
                if not self.effects.reconciles(verified_revision,revision):
                    raise ValueError('Verification receipt is not followed by recorded effects')
                request = replace(request,candidate_revision=verified_revision)
        patches = {u:{p:bytes.fromhex(v) if v is not None else None for p,v in files.items()}
                   for u,files in self.state["patches"].items()}
        self._check_cancel()
        self.active_verification = revision
        prior_activity=dict(self.activity)
        self.activity.update({u:'verifying' for u in self.state['group']})
        try:
            saved=self.effects.call('verify-'+operation,{'request':json.loads(json.dumps(asdict(request)))},
                lambda:asdict(self.verifier(request,self.integration.path,patches)))
            evidence = _verification(saved)
        finally:
            self.active_verification = None
            for unit in self.state['group']:
                if unit in prior_activity:self.activity[unit]=prior_activity[unit]
                else:self.activity.pop(unit,None)
        if evidence.request != request or git(self.integration.path,"rev-parse","HEAD").decode().strip() != revision:
            raise ValueError("Verification returned stale candidate identity")
        self.tdd.assert_frozen() if self.tdd.frozen else None
        ref = self.prefix + "/evidence/" + operation + ".json"
        atomic_write(self.root,ref,json.dumps(asdict(evidence),sort_keys=True).encode())
        self.state.update(verification=asdict(evidence),evidence_ref=ref)
        self._check_cancel()
        return evidence

    def _end(self, outcome: str, reason: str, refs: tuple[str,...]) -> StepResult:
        result = self.review.lifecycle.finish(outcome,candidate_revision=git(self.integration.path,"rev-parse","HEAD").decode().strip(),
                                              reason=reason,evidence_refs=refs)
        return StepResult("ended",self._statuses(),result)

    def _contract_rework(self, defects: tuple[DossierUnit,...], reason: str) -> StepResult:
        if self.contract.contract_version >= self.budget.limits[2]:
            result = BudgetGovernor(self.manager,self.integration,self.budget).abandon(
                reconcile_workers=lambda:True,cycle_exhausted=True,units=defects)
            return StepResult("ended",self._statuses(),result)
        used = self.budget.totals()
        ref = emit_dossier(self.root,self.manager.run_id,self.contract,defects,
            budget_remaining={"input_tokens":max(0,self.budget.limits[0]-used[0]),
                              "output_tokens":max(0,self.budget.limits[1]-used[1])})
        return self._end("rework",reason,(ref.as_posix(),))

    def _failed(self, evidence: VerificationResult, stage: str, operation: str) -> StepResult:
        if evidence.status == "operational":
            return self._end("operational","Verification unavailable",(self.state["evidence_ref"],))
        related = evidence.related_units or tuple(self.state["group"])
        defects = []
        for unit_id in related:
            self._check_cancel()
            unit = self.tdd.units[unit_id]
            judgment=self.effects.call('judge-'+operation+'-'+unit_id,{'request':asdict(evidence.request),'unit':unit_id},
                lambda:dict(zip(('classification','reason'),self.workers.judge(unit,evidence,self._context(),operation+'-judge-'+unit_id))))
            classification, reason = judgment['classification'],judgment['reason']
            failures = evidence.failed_tests or tuple(v.code + ":" + v.file + ":" + v.symbol for v in evidence.violations)
            observation = Observation(evidence.gate,failures, evidence.request.test_selection,
                self.contract.environment_ref.sha256,self.contract.sha256,self.integration.base_revision)
            action = self.retry.evaluate(unit_id,observation,judge_class=classification,stage=stage)
            if action.kind.startswith("restore"):
                changes = {p:bytes.fromhex(v) if v is not None else None for p,v in self.state["snapshots"][unit_id].items()}
                base = git(self.integration.path,"rev-parse","HEAD").decode().strip()
                prior = self.effects.read('apply-'+operation+'-restore-'+unit_id)
                if prior:
                    base = prior['identity']['base']
                self.effects.apply(operation+'-restore-'+unit_id,WorkspaceCandidate(unit_id,self.contract.sha256,base,{},changes))
            defect_class = "contract" if action.defect_class == "contract" or action.kind == "review" else "implementation"
            defects.append(DossierUnit(unit_id,defect_class,unit.spec_ref,evidence.gate,(self.state["evidence_ref"],),
                reason,self.retry.state(unit_id).failed_attempts,tuple(a.trend or "incomparable" for a in self.retry.state(unit_id).history)))
        if any(defect.defect_class == "contract" for defect in defects):
            return self._contract_rework(tuple(defects),"Bounded unit repair requires contract revision")
        self.state["feedback"] = json.dumps({"gate":evidence.gate,"failed":list(evidence.failed_tests)})
        implementers = {u.id:True for u in self.tdd.units.values() if u.role == "impl"}
        unaffected = invalidate_dependents(self.contract,tuple(related),implementers)
        self.state["group"] = sorted(set(implementers) - set(unaffected))
        for unit_id in self.state["group"]:
            self.tdd._states[unit_id] = replace(self.tdd.state(unit_id),stage="green_coding")
        return StepResult("code",self._statuses())

    def _step(self, stage: str, operation: str) -> StepResult:
        if stage in ("repair","rework"):
            record = self.review.state()
            expected = "implementation" if stage == "repair" else "contract"
            evidence = _verification(self.state["verification"])
            if record.get("decision") != expected or record.get("request") != json.loads(json.dumps(asdict(evidence.request))):
                raise ValueError("Review resume identity changed")
            findings = tuple(record.get("findings",()))
            if not findings:
                raise ValueError("Review repair requires findings")
            group = tuple(u.id for u in self.tdd.units.values() if u.role == "impl")
            defects = []
            for unit_id in group:
                unit = self.tdd.units[unit_id]
                action = self.retry.evaluate(unit_id,Observation("tests",tuple("human:" + f for f in findings),
                    evidence.request.test_selection,self.contract.environment_ref.sha256,self.contract.sha256,
                    self.integration.base_revision),judge_class="contract" if stage == "rework" else "implementation",stage="human_repair")
                if stage == "rework" or action.defect_class == "contract":
                    defects.append(DossierUnit(unit_id,"contract",unit.spec_ref,"tests",(self.review.path,),
                        "; ".join(findings),self.retry.state(unit_id).failed_attempts,("human_review",)))
                self.tdd._states[unit_id] = replace(self.tdd.state(unit_id),stage="green_coding")
            if defects:
                return self._contract_rework(tuple(defects),"Human findings require contract revision")
            self.state.update(group=list(group),feedback="Human implementation findings: " + "; ".join(findings))
            return StepResult("code",self._statuses())
        if stage == "prepare":
            for unit in self.tdd.units.values():
                if unit.role != "test":
                    continue
                if self.tdd.state(unit.id).preparation_attempts or any(not confined_path(self.integration.path,p).exists() for p in unit.owns):
                    self._code((unit.id,),"test_authoring",operation + "-" + unit.id)
                try:
                    self._check_cancel()
                    def review_tests() -> dict[str,str]:
                        try:
                            return {'explanation':self.workers.review_tests(unit,self._context(),operation+'-review-'+unit.id)}
                        except TestReviewRejected as exc:
                            return {'rejected':str(exc)}
                    reviewed=self.effects.call('review-'+operation+'-'+unit.id,{'unit':unit.id},
                        review_tests)
                    if 'rejected' in reviewed:
                        raise TestReviewRejected(reviewed['rejected'])
                    explanation = reviewed['explanation']
                except TestReviewRejected as exc:
                    ref = self.prefix + "/evidence/" + operation + "-review-" + unit.id + ".json"
                    atomic_write(self.root,ref,json.dumps({"unit_id":unit.id,"contract_sha256":self.contract.sha256,
                                                           "reason":str(exc),"stage":"test_preparation"}).encode())
                    self.state["feedback"] = str(exc)
                    try:
                        self.tdd.record_preparation_failure(unit.id)
                    except ValueError:
                        if self.tdd.state(unit.id).stage != "preparation_exhausted":
                            raise
                        return self._contract_rework(
                            (DossierUnit(unit.id,"contract",unit.spec_ref,"tests",(ref,),str(exc),
                                         self.tdd.state(unit.id).preparation_attempts,("preparation_exhausted",)),),
                            "Independent test preparation allowance exhausted")
                    return StepResult("prepare",self._statuses())
                self.tdd.approve_tests(unit.id,explanation)
            self.state["patches"] = {}
            return StepResult("red",self._statuses())
        if stage == "red":
            evidence = self._verify(operation,full=True)
            if evidence.status != "operational" and evidence.test_result is not None and evidence.test_result.failure_kind != "assertion":
                failures = set(evidence.test_result.failed)
                authors = {link.author_unit for link in self.contract.test_links if link.test_id in failures}
                authors = authors or {u.id for u in self.tdd.units.values() if u.role == "test"}
                self.state["feedback"] = "Baseline test setup requires repair: " + "; ".join(evidence.test_result.messages)
                defects = []
                for author in sorted(authors):
                    try:
                        self.tdd.record_preparation_failure(author)
                    except ValueError:
                        state = self.tdd.state(author)
                        if state.stage != "preparation_exhausted":
                            raise
                        defects.append(DossierUnit(author,"contract",self.tdd.units[author].spec_ref,"tests",
                            (self.state["evidence_ref"],),self.state["feedback"],state.preparation_attempts,
                            ("preparation_exhausted",)))
                if defects:
                    return self._contract_rework(tuple(defects),"Baseline test preparation allowance exhausted")
                return StepResult("prepare",self._statuses())
            if not evidence.behavioral or evidence.test_result is None:
                return self._end("operational","No behavioral baseline available",(self.state["evidence_ref"],))
            for unit in self.tdd.units.values():
                if unit.role == "impl":
                    self.tdd.record_baseline(unit.id,BehaviorEvidence(evidence.request.candidate_revision,
                        evidence.request.test_selection,evidence.test_result),coverage_review="; ".join(self.tdd._reviews.values()))
            self.tdd.freeze()
            return StepResult("code",self._statuses())
        if stage == "code":
            pending = tuple(u for u in self.tdd.units if self.tdd.state(u).stage == 'pending_shared_verification')
            pending_patches = dict(self.state['patches']) if pending else {}
            group = tuple(u for u in self.state["group"] if self.tdd.state(u).stage == "green_coding") or ready_units(self.tdd)
            for unit_id in group:
                if self.tdd.state(unit_id).stage == "red_evidenced":
                    self.tdd.begin(unit_id)
            self.state["group"] = list(group)
            self._code(group,"green",operation)
            self.state['patches'] = pending_patches | self.state['patches']
            self.state['group'] = list(dict.fromkeys(pending + group))
            members=set(self.state['group'])
            missing={u for link in self.contract.test_links if members.intersection(link.implementing_units)
                     for u in link.implementing_units if u not in members}
            if missing:
                for unit_id in group:self.tdd.pending_shared(unit_id)
                if not ready_units(self.tdd):
                    raise ValueError('Shared candidate group has unsatisfied dependencies')
                return StepResult('code',self._statuses())
            return StepResult("verify",self._statuses())
        if stage in ("verify","final_verify"):
            outstanding=any(u.role=='impl' and u.id not in self.state['group'] and
                            self.tdd.state(u.id).stage!='complete' for u in self.tdd.units.values())
            evidence = self._verify(operation,full=stage == "final_verify" and not outstanding)
            if evidence.status != "passed":
                return self._failed(evidence,stage,operation)
            if evidence.test_result is None or not evidence.behavioral:
                raise ValueError("Passing candidate lacks behavioral execution")
            behavior = BehaviorEvidence(evidence.request.candidate_revision,evidence.request.test_selection,evidence.test_result)
            validate_behavior(behavior,evidence.request.test_selection)
            if stage == "verify":
                self.tdd.record_group_green(tuple(self.state["group"]),behavior)
                for unit_id in self.state["group"]:
                    self.retry.evaluate(unit_id,Observation("tests",(),evidence.request.test_selection,
                        self.contract.environment_ref.sha256,self.contract.sha256,self.integration.base_revision),passed=True)
                return StepResult("refactor",self._statuses())
            for unit_id in self.state["group"]:
                if self.tdd.state(unit_id).stage == "refactor_coding":
                    self.tdd.finish_refactor(unit_id,behavior)
            remaining = any(u.role=="impl" and self.tdd.state(u.id).stage!="complete" for u in self.tdd.units.values())
            return StepResult("code" if remaining else "review",self._statuses())
        if stage == "refactor":
            self._code(tuple(self.state["group"]),"refactor",operation)
            return StepResult("final_verify",self._statuses())
        if stage == "review":
            evidence = _verification(self.state["verification"])
            result = self.review.offer(evidence,self._files(),evidence_refs=(self.state["evidence_ref"],),
                                      package=self.review_package(evidence.request))
            return StepResult("ended",self._statuses(),result)
        if stage == "finalize":
            evidence = _verification(self.state["verification"])
            result = self._complete(evidence.request)
            return StepResult("ended",self._statuses(),result)
        raise ValueError("Unsupported local execution stage")
