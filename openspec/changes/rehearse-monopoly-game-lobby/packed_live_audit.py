"""Qualify final packet packing against exact archived live failure evidence."""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
from evidence_packet import canonical,make_packet
from evidence_context_guard import validate_delivery
from packet_archive import read_packet
from deepseek_context_selector import ContextOptimizer
from context_call_accounting import qualification_envelope
from live_context_audit import LiveReviewAudit
from mixed_backend_pilot import EnvelopeCalls,PILOT_PREFIX
from mixed_backend_policy import clients,active_qualification,profile_sha256,validate_pilot_receipts
from mixed_backend_recovery import CANDIDATE,CONTRACT,verify_preservation
from actual_judge_feedback import validate_finding
from judge_context_adapter import review
from frozen_budget_continuation import check_frozen_sources
from operational_transport import retained_run_reservations
from unity_coder.core.ai_models import ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    source=root/'worktrees/monopoly-game-lobby/integration-v70'
    stopped=json.loads((run/'result.json').read_bytes())
    if (stopped['outcome'] not in ('operational','rework') or stopped['candidate_revision']!=CANDIDATE
        or stopped['contract_sha256']!=CONTRACT or git(source,'rev-parse','HEAD').decode().strip()!=CANDIDATE
        or git(source,'status','--porcelain')):raise ValueError('Exact clean stopped candidate required')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=250000000,output_limit=24000000,
        max_cycles=160,max_added_units=2)
    before=budget._read()
    if len(retained_run_reservations(state,before))!=27:raise ValueError('Reconcile new uncertain effects before qualification')
    frozen=json.loads((run/'services-v70/state.json').read_bytes())['tdd']['frozen']
    check_frozen_sources(source,frozen)
    preserved=json.loads((state/'context-optimization/preservation-v70.json').read_bytes())
    verify_preservation(preserved['budget'],before,preserved['frozen'],frozen)
    operation='v70-step10-verify-judge-ECON';key=sha256(operation.encode()).hexdigest()
    old_verdict=json.loads((state/'context-verdicts'/(key+'.json')).read_bytes())
    old_hash=old_verdict['canonical_sha256']
    original=read_packet(state/'context-packets'/old_hash/'canonical.json',old_hash)
    if (original.identity['candidate']!=CANDIDATE or original.identity['contract']!=CONTRACT
        or original.identity['unit']!='ECON' or original.identity['policy']!=profile_sha256()):
        raise ValueError('Original live review identity changed')
    for item in original.sources:
        if (source/item.path).read_text(encoding='utf-8')!=item.content:raise ValueError('Current source differs from archived evidence')
    packet=make_packet(original.identity|{'packing_format_version':2},original.sources,original.required,
        original.mechanical,original.ownership,original.criteria,original.spec)
    lease=RunLease(state,'monopoly-game-lobby','packed-live-audit-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        qualification=active_qualification(state,budget._read()['calls'])
        effect=json.loads((run/'services-v70/effects'/('judge-v70-step10-verify-ECON.json')).read_bytes())
        receipt=json.loads((run/'model-calls'/(key+'.json')).read_bytes())
        sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
        grant=json.loads((state/'model-authorizations/direct-deepseek-low.json').read_bytes())
        validate_finding(original.mechanical['request'],effect,receipt,sdk,before['calls'][operation],'ECON',grant=grant)
        _,selected,_=clients(framework,root,state,budget)
        calls=EnvelopeCalls(ModelCalls(selected[1],budget,'monopoly-game-lobby'),qualification_envelope(budget,state))
        result=ContextOptimizer(state,qualified=False).run(packet,'ECON');validate_delivery(packet,result)
        op=PILOT_PREFIX+'-live-ECON'
        def send(prompt: str,identity: str) -> dict:
            return json.loads(calls.generate(identity,'ECON',prompt,max_output_tokens=32768).text)
        decision=review(packet,send,op,'defect',initial_input=result.optimized_input,max_calls=1)
        if decision['defect_class']!='contract':
            atomic_write(state,'context-optimization/packed-v2-live-quality-failure.json',canonical({
                'decision':decision,'expected':'contract','canonical_sha256':packet.canonical_sha256}).encode())
            raise ModelError('Live packing missed source-confirmed frozen contract contradictions')
        def shadow() -> dict:
            return review(packet,send,op+'-shadow-audit','defect',max_calls=1)
        audit=LiveReviewAudit(state)
        audit.observe(op,'defect:mixed',packet,result,decision,shadow)
        roles=qualification|{'roles':{'coder':qualification['roles']['coder'],'judge':op}}
        validate_pilot_receipts(state,budget._read()['calls'],roles)
        check_frozen_sources(source,frozen)
        verify_preservation(before,budget._read(),frozen,frozen)
        record={'canonical_parent_sha256':old_hash,'canonical_sha256':packet.canonical_sha256,
            'optimized_sha256':result.optimized_sha256,'decision':decision,'audit_passed':True,
            'free_packing_byte_reduction':result.metrics['byte_reduction'],'reviews_observed':len(audit.read()['reviews']),
            'usage':budget.totals(),'candidate':CANDIDATE,'contract_sha256':CONTRACT,
            'packing_format_version':2,'human_accepted':False,'game_verified':False}
        atomic_write(state,'context-optimization/packed-v2-live-audit.json',canonical(record).encode())
        print(json.dumps(record),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
