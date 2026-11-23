"""Source-only review composition around the unchanged native worker boundary."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
from evidence_packet import Source,Packet,make_packet,canonical
from evidence_context_guard import validate_delivery,owned_review_note
from deepseek_context_selector import ContextOptimizer
from context_call_accounting import CachedSelectionCalls,qualification_envelope
from live_context_audit import LiveReviewAudit,packet_class
from judge_context_adapter import review
from unity_coder.core.ai_models import ModelError
from unity_coder.core.local_executor import TestReviewRejected
from unity_coder.core.workspaces import git
from unity_coder.core.storage import atomic_write
from unity_coder.core.budget import BudgetExhausted
if TYPE_CHECKING:
    from lobby_production_host import ContextWorkers
    from unity_coder.core.contracts import Unit
    from unity_coder.core.model_calls import ModelCalls


def build_review_packet(workers: ContextWorkers,unit: Unit,files: dict[str,str],mechanical: dict,
                        policy: str,mode: str) -> Packet:
    contract=workers.contract
    live=True
    try:candidate=git(workers.root,'rev-parse','HEAD').decode().strip()
    except (ValueError,RuntimeError):
        if (workers.root/'.git').exists():raise
        candidate='uncommitted-offline-fixture'
        live=False
    if live and git(workers.root,'status','--porcelain'):
        raise ModelError('Review requires the exact clean committed candidate')
    def source_text(path: str,provided: str) -> str:
        if not live:return provided
        raw=(workers.root/path).read_bytes()
        if raw!=git(workers.root,'show',candidate+':'+path):raise ModelError('Review source differs from committed candidate')
        text=raw.decode('utf-8')
        if text.replace('\r\n','\n').replace('\r','\n')!=provided.replace('\r\n','\n').replace('\r','\n'):
            raise ModelError('Provided review source is stale or curated unexpectedly')
        return text
    sources=[];required=[]
    ownership={p:u.id for u in contract.units for p in u.owns}
    patches=workers.services.state.get('patches',{})
    patched={path for paths in patches.values() for path in paths}
    # All current source received from the trusted contract context is retained,
    # including complete test partials and helpers. No symbol-guessing omission.
    for path,content in sorted(files.items()):
        if path.startswith(('readonly-','model-calls/')):continue
        if owned_review_note(path,ownership):continue
        content=source_text(path,content)
        if path.endswith('.cs'):
            kind='patched' if path in patched else 'test' if path.startswith('Tests/') else 'dependency'
        elif path==contract.spec.path:continue
        elif path.endswith(('.md','.txt','.json')):
            # Full contract coding-profile rules are mandatory; acceptance maps
            # remain optional supporting documentation, never substitute tests.
            kind='optional' if path.endswith('.acceptance.md') else 'interface'
        else:continue
        identity=sha256(path.encode()).hexdigest()[:24]
        sources.append(Source(identity,path,content,kind))
        if kind!='optional':required.append(identity)
    for path in patched:
        if path.endswith('.cs') and path not in files:raise ModelError('Patched current source absent from Judge canonical context')
    spec=files.get(contract.spec.path)
    if spec is None:raise ModelError('Exact current specification missing')
    spec=source_text(contract.spec.path,spec)
    return make_packet({'run':'monopoly-game-lobby','contract':contract.sha256,'candidate':candidate,
        'unit':unit.id,'stage':mode,'policy':policy,'packing_format_version':2,'source_filter_version':2},tuple(sources),tuple(required),mechanical,
        ownership,tuple(unit.acceptance),spec)


class RehearsalReviews:
    def __init__(self,state: Path,calls: ModelCalls,optimizer_calls: ModelCalls,policy: str,*,qualified_classes: tuple[str,...]=()) -> None:
        self.state,self.calls,self.policy=state,calls,policy
        self.optimizer_calls=optimizer_calls;self.qualified_classes=qualified_classes

    def invoke(self,workers: ContextWorkers,unit: Unit,files: dict[str,str],mechanical: dict,
               operation: str,mode: str) -> dict:
        packet=build_review_packet(workers,unit,files,mechanical,self.policy,mode)
        category=packet_class(mode,mechanical)
        selector=CachedSelectionCalls(self.optimizer_calls,self.state,self.policy)
        qualified=category in self.qualified_classes
        ledger=self.calls.budget
        full_input=self.calls.client.reserve_input(packet.canonical_input)
        # The shared host admission semaphore serializes these budget checks with
        # other coding/review dispatch. Never pay a selector without room for
        # bounded expansion and canonical review from complete source.
        used=ledger.totals()
        worst_input=3*(full_input*2+65536)+self.optimizer_calls.client.reserve_input(packet.canonical_input)
        worst_output=3*32768+8192
        max_calls=3
        audit=LiveReviewAudit(self.state)
        pending_audit=not any(r.get('audit',{}).get('routing_agrees') is True for r in audit.read()['reviews'])
        audit_fits=False
        envelope=qualification_envelope(ledger,self.state)
        if pending_audit:
            try:
                envelope.check(2*full_input+65536+self.optimizer_calls.client.reserve_input(packet.canonical_input),
                    2*32768+8192)
                audit_fits=(used[0]+worst_input+full_input<=ledger.limits[0]
                    and used[1]+worst_output+32768<=ledger.limits[1])
            except ModelError:pass
        qualified=qualified and audit.selection_allowed(category,audit_fits=audit_fits)
        if pending_audit and audit_fits:max_calls=1
        if used[0]+worst_input>ledger.limits[0] or used[1]+worst_output>ledger.limits[1]:
            qualified=False
            max_calls=1
            if used[0]+full_input>ledger.limits[0] or used[1]+32768>ledger.limits[1]:
                raise BudgetExhausted(full_input,32768)
        optimizer=ContextOptimizer(self.state,selector,qualified=qualified)
        result=optimizer.run(packet,unit.id)
        try:validate_delivery(packet,result)
        except ValueError:raise ModelError('Optimizer blocked delivery; inspect the persisted input/check report') from None
        # Expose available canonical references for controlled context requests.
        initial=result.optimized_input+'\nAvailable canonical source references:\n'+canonical([
            {'id':s.id,'path':s.path,'sha256':s.sha256} for s in packet.sources])
        actual_calls=[]
        def send(prompt: str,call: str) -> dict:
            actual_calls.append(call)
            reply=self.calls.generate(call,unit.id,prompt,max_output_tokens=32768)
            try:return json.loads(reply.text)
            except ValueError:raise ModelError('Independent Judge did not return valid JSON') from None
        decision=review(packet,send,operation,mode,initial_input=initial,max_calls=max_calls)
        def shadow() -> dict:
            def shadow_send(prompt: str,call: str) -> dict:
                envelope.check(self.calls.client.reserve_input(prompt),32768)
                reply=self.calls.generate(call,unit.id,prompt,max_output_tokens=32768)
                try:return json.loads(reply.text)
                except ValueError:raise ModelError('Canonical shadow did not return valid JSON') from None
            return review(packet,shadow_send,operation+'-shadow-audit',mode,max_calls=1)
        decision=audit.observe(operation,category,packet,result,decision,
            shadow if pending_audit and audit_fits else None)
        verdict_ref='context-verdicts/'+sha256(operation.encode()).hexdigest()+'.json'
        verdict=canonical({
            'operation':operation,'canonical_sha256':packet.canonical_sha256,
            'optimized_sha256':result.optimized_sha256,'policy':self.policy,'decision':decision,
            'candidate':packet.identity['candidate'],'actual_calls':actual_calls,'final_call':actual_calls[-1],
            'human_accepted':False})
        atomic_write(self.state,verdict_ref,verdict.encode())
        if mode=='defect':
            from architect_finding_index import finding_index
            item={'unit':unit.id,'criterion':list(unit.acceptance),'classification':decision['defect_class'],
                'explanation':decision['explanation'],'evidence':[verdict_ref],'resolved':False,
                'gate':mechanical.get('gate'),'failed_tests':mechanical.get('failed_tests',[])}
            handoff=finding_index(packet.identity['candidate'],packet.identity['contract'],[item],
                list(ledger.totals()),{verdict_ref:verdict})
            atomic_write(self.state,'context-handoffs/'+sha256(operation.encode()).hexdigest()+'.json',canonical(handoff).encode())
        return decision

    def review_tests(self,workers: ContextWorkers,unit: Unit,files: dict[str,str],operation: str) -> str:
        decision=self.invoke(workers,unit,files,{'gate':'source','test_links':[
            asdict(link) for link in workers.contract.test_links if link.author_unit==unit.id]},operation,'test_review')
        if not decision['valid']:raise TestReviewRejected('Independent Judge findings for '+unit.id+': '+decision['explanation'])
        return decision['explanation']

    def judge(self,workers: ContextWorkers,unit: Unit,evidence,files: dict[str,str],operation: str) -> tuple[str,str]:
        mechanical={'gate':evidence.gate,'status':evidence.status,'behavioral':evidence.behavioral,
            'request':asdict(evidence.request),'failed_tests':list(evidence.failed_tests),
            'violations':[asdict(v) for v in evidence.violations],
            'tests':asdict(evidence.test_result) if evidence.test_result else None,
            'related_units':list(evidence.related_units)}
        decision=self.invoke(workers,unit,files,mechanical,operation,'defect')
        return decision['defect_class'],decision['explanation']
