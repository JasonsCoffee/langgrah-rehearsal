"""Prepare a compilable owner-first revision without changing any frozen test."""
from hashlib import sha256
import json
import os
from pathlib import Path
from frozen_implementation_rework import validate_revision
from frozen_budget_continuation import check_frozen_sources
from operational_transport import retained_run_reservations
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    module=root/'module';state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    if (result['outcome']!='rework' or result['contract_version']!=64
        or result['candidate_revision']!='651c60ac70136310b7bc3fda7d17efd9464b1784'
        or result['contract_sha256']!='3736a09ad5d104d5da479ae114e3f8735070999d86a2472f1497efbccb933151'):
        raise ValueError('Exact observed implementation rework required')
    prior_raw=(run/'services-v64/state.json').read_bytes();prior=json.loads(prior_raw);frozen=prior['tdd']['frozen']
    if not frozen or len(frozen)!=185:raise ValueError('Global frozen test set is required')
    evidence_raw=(run/'services-v64/evidence/v64-step5-verify.json').read_bytes();evidence=json.loads(evidence_raw)
    if (evidence['gate']!='compile' or evidence['status']!='failed' or len(evidence['violations'])!=3
        or any(v['file']!='Assets/JJGame/monopoly/Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs' for v in evidence['violations'])):
        raise ValueError('Observed SHELL-only analyzer diagnostics changed')
    dossier_raw=(run/'dossier-v64.json').read_bytes()
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],
        max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    if budget.limits!=[125000000,12000000,80,2]:raise ValueError('Approved limits changed')
    ledger=budget._read();retained=retained_run_reservations(state,ledger)
    if len(retained)!=23:raise ValueError('Unknown reservations changed')
    judgments={}
    for unit in ('SHELL','ECON','MATCH','SOCIAL','RECORDS'):
        call='v64-step5-verify-judge-'+unit;key=sha256(call.encode()).hexdigest()
        raw=(run/'model-calls'/(key+'.json')).read_bytes();receipt=json.loads(raw)
        sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
        decision=json.loads(receipt['reply']['text'])
        if (decision['defect_class']!=('implementation' if unit=='SHELL' else 'contract')
            or receipt['identity']['model']!='gpt-6.1-sol' or receipt['identity']['effort']!='medium'
            or ledger['calls'][call].get('actual')!=[sdk['input_tokens'],sdk['output_tokens']]
            or sdk['text']!=receipt['reply']['text']):raise ValueError('Actual independent Judge directions changed')
        judgments[unit]={'receipt_sha256':sha256(raw).hexdigest(),'decision':decision}
    source=root/'worktrees/architect-v65'
    if source.exists():raise ValueError('Preserve existing preparation and reconcile explicitly')
    git(module,'worktree','add','-b','codex/lobby-architect-v65',str(source),result['candidate_revision'])
    spec=source/'specs/monopoly-game-lobby';previous_raw=(spec/'contract.v64.json').read_bytes();old=json.loads(previous_raw)
    current=json.loads(previous_raw);current.update(contract_version=65,previous_contract_sha256=sha256(previous_raw).hexdigest())
    shell=next(u for u in current['units'] if u['id']=='SHELL')
    retained_files={p:sha256(git(module,'show',result['candidate_revision']+':'+p)).hexdigest() for p in shell['owns']}
    plan=json.loads((run/'services-v64/effects/code-v64-step4-code.json').read_bytes())
    snapshots=plan['snapshots']['SHELL']
    if set(snapshots)!=set(shell['owns']) or plan['base']!='02460607473eb7be1cb5919f3daa1de160c92d0d':
        raise ValueError('Proven pre-Green SHELL snapshot changed')
    restored={}
    for path,encoded in snapshots.items():
        raw=bytes.fromhex(encoded)
        if raw!=git(module,'show',plan['base']+':'+path):raise ValueError('Restoration is not the exact prior baseline')
        (source/path).write_bytes(raw);restored[path]=sha256(raw).hexdigest()
    shell['instructions']+=' Cycle 65 prerequisite repair: the read-only prior delegated SHELL proposal is supplied in readonly-prior-proposal/. Its complete implementation is retained in Git; the current owned files were restored BYTE-FOR-BYTE from the proven pre-Green baseline solely to allow fresh compilable Red. Reapply and repair the full retained proposal, preserving every implemented workflow and existing public API. Address the actual JJCK0011 cancellation-catching diagnostic and both JJCK0005 async-consumption diagnostics. Preserve cancellation propagation and caller await/completion semantics; do not suppress analyzers or replace functionality with stubs. Use the supplied actual compiler diagnostics. Keep all 185 frozen test/configuration files and protected presentation assets unchanged.'
    for unit in current['units']:
        if unit['role']=='impl' and unit['id']!='SHELL':
            unit['depends_on']=list(dict.fromkeys(unit['depends_on']+['SHELL']))
            unit['instructions']+=' Cycle 65 scheduling: SHELL is the prerequisite coding wave. Your existing owned source retains your prior delegated implementation. Preserve it unless actual evidence requires a repair within your ownership; never edit SHELL or frozen tests. Shared-candidate verification runs after all declared co-implementers are integrated. A prerequisite implementation defect owned by a declared peer must be repaired by that peer, without expanding your ownership.'
    validate_revision(old,current,sha256(previous_raw).hexdigest())
    (spec/'contract.v65.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    rules=UnityAdapter();contracts=[]
    for n in range(1,66):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,
        previous=contracts[-1] if contracts else None,max_cycles=80))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    check_frozen_sources(source,frozen)
    for unit in old['units']:
        if unit['role']=='impl' and unit['id']!='SHELL':
            for path in unit['owns']:
                if (source/path).read_bytes()!=git(module,'show',result['candidate_revision']+':'+path):
                    raise ValueError('A retained peer implementation changed')
    git(source,'add','--','specs/monopoly-game-lobby/contract.v65.json',*shell['owns'])
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare frozen owner-first SHELL analyzer repair; retain every delegated proposal')
    manifest={'kind':'implementation_rework','version':65,'previous_services_sha256':sha256(prior_raw).hexdigest(),
        'previous_result_sha256':sha256(result_raw).hexdigest(),'dossier_sha256':sha256(dossier_raw).hexdigest(),
        'frozen':frozen,'retained_candidate':result['candidate_revision'],'retained_proposal_files':retained_files,
        'restored_baseline':plan['base'],'restored_files':restored,'compiler_diagnostics':evidence['violations'],
        'compiler_evidence_sha256':sha256(evidence_raw).hexdigest(),'actual_judge_directions':judgments,
        'human_accepted':False}
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    def reconciled() -> bool:
        retained_run_reservations(state,budget._read());check_frozen_sources(source,frozen)
        tx=json.loads((run/'services-v64/effects/transaction.json').read_bytes())
        return tx['complete'] is True and tx['operation']=='v64-step5-verify' and not git(source,'status','--porcelain')
    lease=RunLease(state,'monopoly-game-lobby','frozen-rework-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'frozen-continuations/v65.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,workers_reconciled=reconciled)
        active={'version':65,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v65','contract_sha256':contract.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'usage':budget.totals(),'limits':budget.limits,'frozen_count':len(frozen),
            'retained_proposal':result['candidate_revision'],'restored_scope':'SHELL only; exact prior baseline; no handwritten implementation','human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
