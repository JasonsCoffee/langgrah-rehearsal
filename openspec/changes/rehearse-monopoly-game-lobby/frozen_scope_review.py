"""Stop unchanged frozen-source retries at a real independent contract rejection."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.dossiers import DossierUnit
from unity_coder.core.executor import StepResult
from unity_coder.core.storage import atomic_write
from frozen_budget_continuation import check_frozen_sources


def eligible(owns: tuple[str,...],frozen: dict[str,str],attempts: int,decision: dict) -> bool:
    return (bool(owns) and set(owns)<=set(frozen) and attempts>0
        and decision.get('valid') is False and isinstance(decision.get('explanation'),str)
        and bool(decision['explanation'].strip()))


class FrozenScopeServices:
    def __init__(self,inner,state: Path,frozen: dict[str,str]) -> None:
        self.inner,self.root,self.frozen=inner,state,frozen

    def __getattr__(self,name: str):return getattr(self.inner,name)

    def _route(self,stage: str,operation: str) -> StepResult | None:
        if stage!='prepare' or self.inner.tdd.frozen:return None
        saved=self.root/('frozen-review-routing/v'+str(self.inner.contract.contract_version)+'/'+operation+'.json')
        if saved.exists():
            from unity_coder.core.workspaces import git
            cached=json.loads(saved.read_bytes());key=sha256(cached['actual_judge_call'].encode()).hexdigest()
            if (cached['contract_sha256']!=self.inner.contract.sha256
                or cached['candidate']!=git(self.inner.integration.path,'rev-parse','HEAD').decode().strip()
                or cached['paid_sha256']!=sha256((self.root/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json')).read_bytes()).hexdigest()
                or cached['sdk_sha256']!=sha256((self.root/'codex-receipts'/(key+'.json')).read_bytes()).hexdigest()):
                raise ValueError('Persisted frozen rejection provenance changed')
            check_frozen_sources(self.inner.integration.path,self.frozen)
            return StepResult(**cached['report'])
        feedback=self.inner.state.get('feedback','')
        for unit in self.inner.contract.units:
            if getattr(unit,'status','active')!='active':continue
            attempts=self.inner.tdd.state(unit.id).preparation_attempts
            if unit.role!='test' or not attempts or not set(unit.owns)<=set(self.frozen):continue
            for effect in (self.root/self.inner.prefix/'effects').glob('review-*-'+unit.id+'.json'):
                record=json.loads(effect.read_bytes())
                if record.get('identity')!={'unit':unit.id} or record.get('result',{}).get('rejected')!=feedback:continue
                previous=effect.name[len('review-'):-(len(unit.id)+6)]
                review_operation=previous+'-review-'+unit.id
                verdict_path=self.root/'context-verdicts'/(sha256(review_operation.encode()).hexdigest()+'.json')
                if not verdict_path.exists():continue
                verdict=json.loads(verdict_path.read_bytes());decision=verdict['decision']
                if not eligible(unit.owns,self.frozen,attempts,decision):continue
                from unity_coder.core.workspaces import git
                candidate=git(self.inner.integration.path,'rev-parse','HEAD').decode().strip()
                if (verdict['candidate']!=candidate or verdict['operation']!=review_operation
                    or verdict['policy']!=self.inner.workers.context_reviews.policy
                    or feedback!='Independent Judge findings for '+unit.id+': '+decision['explanation']):
                    raise ValueError('Frozen rejection has stale source/policy identity')
                from packet_archive import read_packet
                identity=verdict['canonical_sha256']
                packet=read_packet(self.root/'context-packets'/identity/'canonical.json',identity)
                if (packet.identity['contract']!=self.inner.contract.sha256 or packet.identity['unit']!=unit.id
                    or packet.identity['candidate']!=candidate
                    or packet.mechanical.get('unit_instructions')!=unit.instructions):
                    raise ValueError('Frozen rejection lacks the complete current contract authority')
                run=self.root/'.agent/runs/monopoly-game-lobby';call=verdict['final_call'];key=sha256(call.encode()).hexdigest()
                paid=json.loads((run/'model-calls'/(key+'.json')).read_bytes())
                sdk=json.loads((self.root/'codex-receipts'/(key+'.json')).read_bytes())
                charge=self.inner.budget._read()['calls'][call]
                if (paid['identity']['role']!='judge' or paid['identity']['model']!='gpt-6.1-sol'
                    or paid['identity']['effort']!='low' or json.loads(paid['reply']['text'])!=decision
                    or sdk['text']!=paid['reply']['text']
                    or sdk['policy_sha256']!=paid['identity']['backend_policy_sha256']
                    or charge.get('actual')!=[sdk['input_tokens'],sdk['output_tokens']]):
                    raise ValueError('Frozen rejection lacks actual independent settled receipt')
                check_frozen_sources(self.inner.integration.path,self.frozen)
                self.inner.preflight()
                refs=tuple(str(p.relative_to(self.root)).replace('\\','/') for p in (effect,verdict_path))
                finding=DossierUnit(unit.id,'contract',unit.spec_ref,'tests',refs,
                    decision['explanation']+' This owned source is completely frozen; further unchanged author/review retries cannot repair it. A consecutive authorized contract scope is required.',
                    attempts,('actual_frozen_source_review_rejection',))
                report=self.inner._contract_rework((finding,),'Independent rejection requires new scope; unchanged frozen retries stopped')
                self.inner._save()
                atomic_write(self.root,str(saved.relative_to(self.root)).replace('\\','/'),json.dumps({
                    'report':asdict(report),'actual_judge_call':call,'new_paid_call':False,
                    'contract_sha256':self.inner.contract.sha256,'candidate':candidate,
                    'paid_sha256':sha256((run/'model-calls'/(key+'.json')).read_bytes()).hexdigest(),
                    'sdk_sha256':sha256((self.root/'codex-receipts'/(key+'.json')).read_bytes()).hexdigest(),
                    'test_files_changed':False,'human_accepted':False},sort_keys=True).encode())
                print('Routed actual frozen-source rejection without unchanged paid retries',unit.id,flush=True)
                return report
        return None

    def step(self,stage: str,operation: str) -> StepResult:
        report=self._route(stage,operation)
        return report if report is not None else self.inner.step(stage,operation)

    def reconcile(self,stage: str,operation: str) -> StepResult:
        # The first v73 guard failure occurred before LocalExecutionServices was
        # entered. Prove that exact empty boundary before starting its transaction.
        if (stage=='prepare' and operation=='v73-step1-prepare'
            and self.inner.effects.read('transaction') is None):
            from unity_coder.core.workspaces import git
            ledger=self.inner.budget._read()
            effects=self.root/self.inner.prefix/'effects'
            if (self.inner.contract.sha256!='80633a01b3edf2c72c6aefac09c960d08b024756ec51af748f7372ee60e0402a'
                or any(c['version']==73 for c in ledger['calls'].values())
                or (effects.exists() and any(effects.iterdir()))
                or any(s.preparation_attempts for s in self.inner.tdd._states.values())
                or git(self.inner.integration.path,'rev-parse','HEAD').decode().strip()!='3f1baaa616ddb2a533c1f6b32ebce7ef96a66c37'
                or git(self.inner.integration.path,'status','--porcelain')):
                raise ValueError('Empty first-prepare recovery lost its no-effects proof')
            check_frozen_sources(self.inner.integration.path,self.frozen)
            atomic_write(self.root,'host-reconciliations/v73-empty-first-prepare.json',json.dumps({
                'operation':operation,'contract_sha256':self.inner.contract.sha256,
                'candidate':'3f1baaa616ddb2a533c1f6b32ebce7ef96a66c37','model_calls_in_cycle':0,
                'effects_before_reconcile':0,'source_changed':False,'human_accepted':False},sort_keys=True).encode())
            return self.inner.step(stage,operation)
        report=self._route(stage,operation)
        return report if report is not None else self.inner.reconcile(stage,operation)
