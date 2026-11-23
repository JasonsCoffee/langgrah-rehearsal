"""Consecutive transition for two approved acceptance corrections; no model calls."""
from hashlib import sha256
import json
import os
from pathlib import Path
from approved_test_reconciliation_v71 import PREVIOUS_SHA,REPLY,SCOPE,PROFILE,PROTOCOL,author_paths,validate_revision,updated_profile
from frozen_budget_continuation import check_frozen_sources
from lobby_budget_period import period_usage
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
    if (result['outcome']!='rework' or result['contract_version']!=70 or result['contract_sha256']!=PREVIOUS_SHA
        or result['candidate_revision']!='625db77bf4e75060435947d955328a729f6f87dc'):
        raise ValueError('Exact paid cycle-70 rework required')
    candidate=result['candidate_revision'];baseline='7dbcc44152f058fa60d348064a6bb389b3a3c514'
    prior_raw=(run/'services-v70/state.json').read_bytes();frozen=json.loads(prior_raw)['tdd']['frozen']
    dossier_raw=(run/'dossier-v70.json').read_bytes()
    if len(frozen)!=199:raise ValueError('Retain the complete prior global freeze')
    prior_integration=root/'worktrees/monopoly-game-lobby/integration-v70'
    check_frozen_sources(prior_integration,frozen)
    if git(prior_integration,'rev-parse','HEAD').decode().strip()!=candidate or git(prior_integration,'status','--porcelain'):
        raise ValueError('Prior integration drift')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],
        max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    before=budget._read();period_usage(state,before)
    if budget.limits!=[190044520,8520897,120,2] or len(retained_run_reservations(state,before))!=27:
        raise ValueError('Fresh authorized period and all unknown charges required')
    red=json.loads((run/'services-v70/evidence/v70-step2-red.json').read_bytes())
    if red['request']['candidate_revision']!=baseline or red['behavioral'] is not True:
        raise ValueError('Proven compilable behavioral Red baseline required')
    source=root/'worktrees/architect-v71'
    if source.exists():
        if (git(source,'rev-parse','HEAD').decode().strip()!=baseline
            or git(source,'branch','--show-current').decode().strip()!='codex/lobby-architect-v71'):
            raise ValueError('Existing preparation identity changed')
        changed=git(source,'status','--porcelain').decode().splitlines()
        if set(changed)!={' M specs/monopoly-game-lobby/binding-protocol.v2.md','?? specs/monopoly-game-lobby/contract.v71.json'}:
            raise ValueError('Only the exact failed profile preflight may resume')
        original=git(module,'show',baseline+':specs/monopoly-game-lobby/binding-protocol.v2.md')
        protocol_path=source/'specs/monopoly-game-lobby/binding-protocol.v2.md'
        if protocol_path.read_bytes()!=original.replace(b'Friends, day ranking, history',b'Friends, weekly ranking, history'):
            raise ValueError('Failed preparation clause changed')
        protocol_path.write_bytes(original)
    else:
        git(module,'worktree','add','-b','codex/lobby-architect-v71',str(source),baseline)
    check_frozen_sources(source,frozen)
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v70.json').read_bytes();old=json.loads(old_raw)
    if sha256(old_raw).hexdigest()!=PREVIOUS_SHA:raise ValueError('Previous contract drift')
    current=json.loads(old_raw);current.update(contract_version=71,previous_contract_sha256=PREVIOUS_SHA)
    directions={
      'TEST-PRES-CORE': 'Inside Story_L1_03 ONLY, change ranking Menu Row1 expected initial tab from day to week, matching original US-L5-01 and the independently covered weekly default. Preserve every other route, pointer, menu, tab-switch, scroll and geometry assertion.',
      'TEST-PRES-NFR': 'Inside Story_NFR_01 ONLY, keep all three viewport/safe-area iterations. On Recharge, assert Primary (the wallet plus) is inactive instead of calling the helper that requires it active. Preserve Coins and Ingots visibility/geometry on Recharge and Primary safe-area checks on every other screen. Preserve all other checks including Tab0, layout distortion, popup/scene and responsive signatures. Do not change any helper or add business behavior.'}
    for unit in current['units']:
        if unit['id'] in SCOPE:
            paths=author_paths(unit['id']);guid=sha256(paths[1].encode()).hexdigest()[:32]
            unit['owns']+=list(paths[1:])
            unit['instructions']+='\nCYCLE 71 EXPLICIT USER-APPROVED TWO-CONFLICT RECONCILIATION. '+directions[unit['id']]+' Every byte outside the approved method body is frozen, including attributes and signatures. Write '+paths[1]+' with source rationale and preserved coverage, and '+paths[2]+' exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Omit historical notes from output. Only the Coder may implement these assertions; independent review and fresh Red must pass before global freeze.'
        elif unit['role']=='impl':
            unit['instructions']+='\nCycle 71: preserve and repair your complete prior paid implementation supplied read-only. Current source is the exact proven pre-Green baseline for fresh Red, not a request for new stubs. Two approved assertions now match original requirements: Recharge wallet plus hidden; ranking menu defaults to week. Every test is frozen before your dispatch. Repair actual failures within your ownership, coordinate through declared peers, never modify tests, weaken behavior or withhold owned functionality because a peer also needs repair.'
    protocol=spec/'binding-protocol.v2.md';raw=protocol.read_bytes()
    if raw.count(b'Friends, day ranking, history')!=1:raise ValueError('Exact conflicting binding clause required')
    revised=raw.replace(b'Friends, day ranking, history',b'Friends, weekly ranking, history')
    (source/PROTOCOL).write_bytes(revised)
    profile=updated_profile(json.loads((source/old['coding_profile_ref']['path']).read_bytes()),sha256(revised).hexdigest())
    profile_raw=(json.dumps(profile,ensure_ascii=False,indent=2)+'\n').encode()
    (source/PROFILE).write_bytes(profile_raw)
    current['coding_profile_ref']={'path':PROFILE,'sha256':sha256(profile_raw).hexdigest()}
    validate_revision(old,current)
    (spec/'contract.v71.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    rules=UnityAdapter();contracts=[]
    for number in range(1,72):
        contracts.append(load_contract((spec/('contract.v'+str(number)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=120))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    git(source,'add','specs/monopoly-game-lobby/contract.v71.json',PROFILE,PROTOCOL)
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare two approved source-backed acceptance corrections')
    approval={'authority':'explicit_user_session','reply':REPLY,'version':71,'scope':SCOPE}
    protected={p:h for p,h in frozen.items() if p not in {item['path'] for item in SCOPE.values()}}
    owned={u.id:list(u.owns) for u in contract.units if u.role=='impl' and u.status=='active'}
    manifest={'kind':'approved_test_reconciliation_v71','version':71,'scope':SCOPE,'frozen':frozen,
        'previous_services_sha256':sha256(prior_raw).hexdigest(),'previous_result_sha256':sha256(result_raw).hexdigest(),
        'dossier_sha256':sha256(dossier_raw).hexdigest(),'human_accepted':False}
    restoration={'state':'complete','baseline':baseline,'retained_candidate':candidate,'owned':owned,'tests':protected,
        'retained_proposals':{u:{p:sha256(git(module,'show',candidate+':'+p)).hexdigest() for p in paths} for u,paths in owned.items()},
        'previous_evidence':json.loads((run/'services-v70/evidence/v70-step10-verify.json').read_bytes()),
        'independent_findings':json.loads(dossier_raw)['failed_units'],
        'note':'Current runtime is the exact prior cycle-70 behavioral Red baseline. Full prior paid implementations are retained verbatim as read-only proposals; reapply and repair YOUR owned files. Preserve every workflow and address actual owner-specific failures. Only the two approved test methods may change during preparation; all tests become immutable again before coding. Other reported test-contract defects require independent source diagnosis and separate authorization, never silent weakening. Full sequential verification and independent judgment remain mandatory.'}
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    def reconciled() -> bool:
        check_frozen_sources(prior_integration,frozen);check_frozen_sources(source,frozen)
        tx=json.loads((run/'services-v70/effects/transaction.json').read_bytes())
        return tx['complete'] is True and tx['operation']=='v70-step10-verify' and len(retained_run_reservations(state,budget._read()))==27 and not git(source,'status','--porcelain')
    lease=RunLease(state,'monopoly-game-lobby','approved-reconciliation-v71-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'model-authorizations/test-reconciliation-v71.json',json.dumps(approval,indent=2).encode())
        atomic_write(state,'frozen-continuations/v71.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v71.json',json.dumps(restoration,indent=2).encode())
        active={'version':71,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v71','contract_sha256':contract.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'token_period_usage':period_usage(state,budget._read())[0],
            'prior_frozen_files':199,'still_protected':len(protected),'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
