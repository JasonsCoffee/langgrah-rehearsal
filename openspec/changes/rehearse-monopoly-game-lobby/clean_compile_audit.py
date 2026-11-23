"""Clean-source shadow audit of real archived compilation, without game execution."""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
from evidence_packet import Source,Packet,make_packet,canonical
from evidence_context_guard import validate_delivery,private_note_ids
from deepseek_context_selector import ContextOptimizer
from live_context_audit import LiveReviewAudit
from mixed_backend_policy import clients,active_qualification,profile_sha256,activate_backend,validate_pilot_receipts
from mixed_backend_recovery import CANDIDATE,CONTRACT,verify_preservation
from mixed_backend_pilot import EnvelopeCalls
from context_call_accounting import qualification_envelope
from judge_context_adapter import review
from frozen_budget_continuation import check_frozen_sources
from operational_transport import retained_run_reservations
from unity_coder.core.ai_models import ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.workspaces import git

AUDIT_OPERATION='v70-migration-packed-v2-clean-compile-ECON'
EVIDENCE_CANDIDATE='be19106e61f8c5ce78cdde53803573616b9334fb'


def compile_packet(root: Path,state: Path) -> Packet:
    module=root/'module';run=state/'.agent/runs/monopoly-game-lobby'
    raw=(run/'services-v70/evidence/v70-step5-verify.json').read_bytes()
    if sha256(raw).hexdigest()!='256665687bfeea499594fab1268be0b4a878f3d1d10bb66a13c7331440ecda0d':
        raise ValueError('Archived real compiler evidence changed')
    mechanical=json.loads(raw)
    if (mechanical['gate']!='compile' or mechanical['status']!='failed'
        or mechanical['request']['candidate_revision']!=EVIDENCE_CANDIDATE
        or mechanical['request']['contract_sha256']!=CONTRACT or mechanical['test_result'] is not None):
        raise ValueError('Exact historical compilation and no test execution required')
    def blob(path: str) -> bytes:return git(module,'show',EVIDENCE_CANDIDATE+':'+path)
    contract_raw=blob('specs/monopoly-game-lobby/contract.v70.json')
    if sha256(contract_raw).hexdigest()!=CONTRACT:raise ValueError('Historical contract changed')
    contract=json.loads(contract_raw);ownership={p:u['id'] for u in contract['units'] for p in u['owns']}
    patched={p for u in contract['units'] if u['role']=='impl' and u['status']=='active' for p in u['owns']}
    profile_ref=contract['coding_profile_ref'];profile_raw=blob(profile_ref['path'])
    if sha256(profile_raw).hexdigest()!=profile_ref['sha256']:raise ValueError('Historical coding profile changed')
    profile=json.loads(profile_raw)
    paths=set(patched)|{profile_ref['path']}
    for item in profile['rules']:
        if sha256(blob(item['path'])).hexdigest()!=item['sha256']:raise ValueError('Historical rule identity changed')
        paths.add(item['path'])
    names=git(module,'ls-tree','-r','--name-only','-z',EVIDENCE_CANDIDATE,'--',
        'Runtime/Script/UI/LobbyRehearsal').decode().split('\0')
    paths.update(p for p in names if p.endswith('.cs'))
    sources=tuple(Source(sha256(path.encode()).hexdigest()[:24],path,blob(path).decode('utf-8'),
        'patched' if path in patched else 'dependency' if path.endswith('.cs') else 'interface') for path in sorted(paths))
    spec=blob(contract['spec_ref'])
    if sha256(spec).hexdigest()!=contract['spec_sha256']:raise ValueError('Historical spec identity changed')
    unit=next(u for u in contract['units'] if u['id']=='ECON')
    packet=make_packet({'run':'monopoly-game-lobby','contract':CONTRACT,'candidate':EVIDENCE_CANDIDATE,
        'unit':'ECON','stage':'defect','policy':profile_sha256(),'packing_format_version':2,
        'source_filter_version':2,'scope':'real_archived_compilation_only'},sources,tuple(s.id for s in sources),
        mechanical,ownership,tuple(unit['acceptance']),spec.decode('utf-8'))
    if private_note_ids(packet):raise ValueError('Private author reports reached clean compile audit')
    return packet


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    source=root/'worktrees/monopoly-game-lobby/integration-v70'
    result=json.loads((run/'result.json').read_bytes())
    if (result['outcome']!='rework' or result['candidate_revision']!=CANDIDATE or result['contract_sha256']!=CONTRACT
        or git(source,'rev-parse','HEAD').decode().strip()!=CANDIDATE or git(source,'status','--porcelain')):
        raise ValueError('Preserve current clean native rework; no new game execution')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=250000000,output_limit=24000000,max_cycles=160,max_added_units=2)
    before=budget._read();frozen=json.loads((run/'services-v70/state.json').read_bytes())['tdd']['frozen']
    check_frozen_sources(source,frozen)
    preserved=json.loads((state/'context-optimization/preservation-v70.json').read_bytes())
    verify_preservation(preserved['budget'],before,preserved['frozen'],frozen)
    if len(retained_run_reservations(state,before))!=27:raise ValueError('Reconcile any new uncertain call first')
    packet=compile_packet(root,state)
    lease=RunLease(state,'monopoly-game-lobby','clean-compile-audit-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        qualification=active_qualification(state,budget._read()['calls'])
        _,selected,_=clients(framework,root,state,budget)
        calls=EnvelopeCalls(ModelCalls(selected[1],budget,'monopoly-game-lobby'),qualification_envelope(budget,state))
        optimized=ContextOptimizer(state,qualified=False).run(packet,'ECON');validate_delivery(packet,optimized)
        def send(prompt: str,call: str) -> dict:
            return json.loads(calls.generate(call,'ECON',prompt,max_output_tokens=32768).text)
        decision=review(packet,send,AUDIT_OPERATION,'defect',initial_input=optimized.optimized_input,max_calls=1)
        if decision['defect_class']!='implementation':raise ModelError('Clean compile audit did not identify the proven owned serializer defect')
        def shadow() -> dict:return review(packet,send,AUDIT_OPERATION+'-shadow-audit','defect',max_calls=1)
        observer=LiveReviewAudit(state)
        observer.observe(AUDIT_OPERATION,'defect:compile',packet,optimized,decision,shadow,force_audit=True)
        for call in (AUDIT_OPERATION,AUDIT_OPERATION+'-shadow-audit'):
            validate_pilot_receipts(state,budget._read()['calls'],qualification|{
                'roles':{'coder':qualification['roles']['coder'],'judge':call}})
        check_frozen_sources(source,frozen);verify_preservation(before,budget._read(),frozen,frozen)
        report={'audit_passed':True,'packing_format_version':2,'source_filter_version':2,
            'current_candidate':CANDIDATE,'evidence_candidate':EVIDENCE_CANDIDATE,'contract_sha256':CONTRACT,
            'evidence_request':'v70-step5-verify','canonical_sha256':packet.canonical_sha256,
            'optimized_sha256':optimized.optimized_sha256,'check_results':optimized.check_results,
            'decision':decision,'sources':len(packet.sources),'reviews_observed':len(observer.read()['reviews']),
            'canonical_bytes':len(packet.canonical_input.encode()),'delivered_bytes':len(optimized.optimized_input.encode()),
            'usage':budget.totals(),'game_verified':False,'human_accepted':False}
        atomic_write(state,'context-optimization/packed-v2-clean-compile-audit.json',canonical(report).encode())
        activate_backend(state,budget)
        print(json.dumps(report),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
