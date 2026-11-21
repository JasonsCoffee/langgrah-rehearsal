"""Prepare exact paid implementation bases only after genuine cycle-69 rework."""
from hashlib import sha256
import json
import os
from pathlib import Path
from actual_judge_feedback import validate_finding
from frozen_budget_continuation import check_frozen_sources
from frozen_implementation_rework import complete_inventory,validate_revision
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


def commit(source: Path,message: str,paths: list[str]) -> str:
    git(source,'add','--',*paths)
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m',message)
    return git(source,'rev-parse','HEAD').decode().strip()


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';module=root/'module';run=state/'.agent/runs/monopoly-game-lobby'
    result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    expected='e4db83d9eed559a43be0a4b3c1626494b90e8d4322097510d144ef2ae53d9b9e'
    if result['outcome']!='rework' or result['contract_version']!=69 or result['contract_sha256']!=expected:
        raise ValueError('Only actual native cycle-69 rework may advance; never interrupt a live operation')
    candidate=result['candidate_revision'];current=root/'worktrees/monopoly-game-lobby/integration-v69'
    if git(current,'rev-parse','HEAD').decode().strip()!=candidate or git(current,'status','--porcelain'):
        raise ValueError('Actual previous candidate must remain clean and exact')
    coordinator='Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs'
    known_stub=git(module,'show','715fe9b9ea7aaf60034acb6cc833c2cd5ec10aa8:'+coordinator)
    if (current/coordinator).read_bytes()!=known_stub:
        raise ValueError('A newer paid coordinator exists; revise preparation to preserve that exact source before transitioning')
    prior_raw=(run/'services-v69/state.json').read_bytes();prior=json.loads(prior_raw)
    frozen=prior['tdd']['frozen'];old_raw=(current/'specs/monopoly-game-lobby/contract.v69.json').read_bytes()
    old=json.loads(old_raw);complete_inventory(old,frozen,frozen);check_frozen_sources(current,frozen)
    if (len(frozen)!=199 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!=
        '2da65db6815d61fb277a19f826b4d512e78c8bc4dc2f4f8c4d1b3387e8d1c520'):
        raise ValueError('The complete globally frozen cycle-69 inventory changed')
    dossier_raw=(run/'dossier-v69.json').read_bytes();dossier=json.loads(dossier_raw)
    if dossier['reason']!='rework' or not dossier['failed_units']:raise ValueError('Actual native dossier required')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=250000000,output_limit=24000000,max_cycles=160,max_added_units=2)
    ledger=budget._read()
    if len(retained_run_reservations(state,ledger))!=25:raise ValueError('All uncertain reservations must remain')
    findings={};evidences={}
    for failed in dossier['failed_units']:
        unit=failed['id']
        if failed['defect_class']!='contract' or not failed['evidence_refs']:raise ValueError('Bounded escalation required')
        ref=failed['evidence_refs'][-1];raw=(state/ref).read_bytes();evidence=json.loads(raw)
        if evidence['request']['candidate_revision']!=candidate or evidence['status']!='failed':
            raise ValueError('Dossier must retain actual failed-candidate evidence')
        operation=evidence['request']['request_id'];call=operation+'-judge-'+unit;key=sha256(call.encode()).hexdigest()
        effect=json.loads((run/('services-v69/effects/judge-'+operation+'-'+unit+'.json')).read_bytes())
        receipt=json.loads((run/'model-calls'/(key+'.json')).read_bytes())
        sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
        finding=validate_finding(evidence['request'],effect,receipt,sdk,ledger['calls'][call],unit)
        if effect['result']['classification']!='implementation':
            raise ValueError('A genuine Judge contract finding needs separate Architect analysis')
        findings[unit]={'classification':'implementation','reason':finding};evidences[operation]=evidence
    transaction=json.loads((run/'services-v69/effects/transaction.json').read_bytes())
    if transaction['complete'] is not True:raise ValueError('No native transition during an incomplete operation')
    source=root/'worktrees/architect-v70';reference=root/'worktrees/paid-reference-v70'
    if source.exists() or reference.exists():raise ValueError('Preserve existing preparation; reconcile it explicitly')
    owned={u['id']:list(u['owns']) for u in old['units'] if u['role']=='impl' and u['status']=='active'}
    # The old descriptor preserves full model-source hashes and actual compiler/Judge provenance.
    paid=json.loads((state/'baseline-restorations/v69.json').read_bytes())
    if paid['retained_candidate']!='830e171a6838ab07961d385bdc4be47b6a162ce5' or set(paid['owned']['SHELL'])!=set(owned['SHELL']):
        raise ValueError('Known complete paid SHELL proposal provenance required')
    git(module,'worktree','add','-b','codex/lobby-paid-reference-v70',str(reference),candidate)
    for path in owned['SHELL']:
        raw=git(module,'show',paid['retained_candidate']+':'+path)
        if sha256(raw).hexdigest()!=paid['retained_proposals']['SHELL'][path]:raise ValueError('Paid source changed')
        (reference/path).write_bytes(raw)
    retained=commit(reference,'Retain exact paid complete SHELL source for delegated repair',owned['SHELL'])
    check_frozen_sources(reference,frozen)
    git(module,'worktree','add','-b','codex/lobby-architect-v70',str(source),candidate)
    new=json.loads(old_raw);new.update(contract_version=70,previous_contract_sha256=sha256(old_raw).hexdigest())
    instruction=('\nCYCLE 70 COMPLETE SOURCE REPAIR: current runtime was restored to exact proven Red bytes. '
        'Reapply the complete paid owned base supplied by the trusted transport, retaining all workflows. '
        'SHELL must use the final hash-bound edit protocol and explicitly accept all restored bases. '
        'Do not return a compile-only method while leaving coordinator stubs. Repair actual compilation '
        'and every mapped functional behavior. JJCK0011 requires the supported is-not cancellation '
        'filter syntax; the older negated-is sample is rejected by the active analyzer. Preserve '
        'cancellation propagation, async completion and the generated lifecycle block within OnDestroy. '
        'All 199 frozen files, tests, ownership and presentation assets remain unchanged.')
    for unit in new['units']:
        if unit['role']=='impl':unit['instructions']+=instruction
    validate_revision(old,new,sha256(old_raw).hexdigest())
    spec=source/'specs/monopoly-game-lobby'
    (spec/'contract.v70.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    baseline='4333140e62c550bd3fc0050d83b6abf24c89770e'
    for paths in owned.values():
        for path in paths:(source/path).write_bytes(git(module,'show',baseline+':'+path))
    check_frozen_sources(source,frozen)
    rules=UnityAdapter();contracts=[]
    for version in range(1,71):
        contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=160))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    prepared=commit(source,'Preserve complete frozen inventory and prepare paid-source delegated repair',
        ['specs/monopoly-game-lobby/contract.v70.json']+[p for paths in owned.values() for p in paths])
    manifest={'kind':'implementation_rework','version':70,'source_revision':candidate,'frozen':frozen,
        'previous_services_sha256':sha256(prior_raw).hexdigest(),'previous_result_sha256':sha256(result_raw).hexdigest(),
        'dossier_sha256':sha256(dossier_raw).hexdigest(),'retained_candidate':retained,
        'retained_proposal_files':{},'compiler_diagnostics':[], 'human_accepted':False}
    restoration={'state':'complete','baseline':baseline,'retained_candidate':retained,'owned':owned,'tests':frozen,
        'retained_proposals':{u:{p:sha256(git(module,'show',retained+':'+p)).hexdigest() for p in paths} for u,paths in owned.items()},
        'previous_evidence':evidences,'independent_findings':findings,'note':instruction}
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    def reconciled() -> bool:
        check_frozen_sources(current,frozen);check_frozen_sources(source,frozen)
        return not git(source,'status','--porcelain') and len(retained_run_reservations(state,budget._read()))==25
    lease=RunLease(state,'monopoly-game-lobby','complete-repair-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'frozen-continuations/v70.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v70.json',json.dumps(restoration,indent=2).encode())
        active={'version':70,'candidate':prepared,'contract_source':'architect-v70','contract_sha256':contract.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        if any(budget._read()['calls'].get(k)!=v for k,v in ledger['calls'].items()):raise ValueError('Historical charges changed')
        print(json.dumps(active|{'usage':budget.totals(),'limits':budget.limits,'frozen_preserved':len(frozen),
            'retained_candidate':retained,'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
