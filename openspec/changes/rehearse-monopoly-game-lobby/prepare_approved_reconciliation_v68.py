"""Native same-run transition for the user's method-bounded test approval."""
from hashlib import sha256
import json
import os
from pathlib import Path
from approved_test_reconciliation import PREVIOUS_SHA,REPLY,SCOPE,author_paths,validate_authority,validate_revision
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
    dossier_raw=(run/'dossier-v67.json').read_bytes();dossier=json.loads(dossier_raw)
    approval={'authority':'explicit_user_session','reply':REPLY,'version':68,'scope':SCOPE}
    validate_authority(approval,result,dossier)
    candidate='9291bdd5fd5c2ed1a0875073dea334529f12b4ae'
    if result['candidate_revision']!=candidate:raise ValueError('Observed rework candidate changed')
    prior_raw=(run/'services-v67/state.json').read_bytes();frozen=json.loads(prior_raw)['tdd']['frozen']
    if len(frozen)!=189 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!='03aeaba0e7597069ab59c1a98f9b0a664f3f7e7ff64e73c36d5939779fce32c5':
        raise ValueError('Previous global freeze changed')
    prior_integration=root/'worktrees/monopoly-game-lobby/integration-v67'
    check_frozen_sources(prior_integration,frozen)
    if git(prior_integration,'rev-parse','HEAD').decode().strip()!=candidate or git(prior_integration,'status','--porcelain'):
        raise ValueError('Previous integration changed')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=250000000,output_limit=24000000,max_cycles=160,max_added_units=2)
    before=budget._read();retained=retained_run_reservations(state,before)
    if len(retained)!=25:raise ValueError('All uncertain reservations must remain')
    call='v67-step6-verify-judge-SHELL';key=sha256(call.encode()).hexdigest()
    receipt_raw=(run/'model-calls'/(key+'.json')).read_bytes();receipt=json.loads(receipt_raw)
    sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
    decision=json.loads(receipt['reply']['text'])
    if (decision['defect_class']!='contract' or receipt['identity']['model']!='gpt-6.1-sol'
        or receipt['identity']['effort']!='medium' or sdk['text']!=receipt['reply']['text']
        or before['calls'][call].get('actual')!=[sdk['input_tokens'],sdk['output_tokens']]):
        raise ValueError('Actual paid independent contract finding required')
    source=root/'worktrees/architect-v68';reference=root/'worktrees/paid-reference-v68'
    if source.exists() or reference.exists():raise ValueError('Preserve existing paths and reconcile explicitly')
    baseline='1864d5b240a6ccfe36e8ba06fabdbb6f076c206b'
    git(module,'worktree','add','-b','codex/lobby-architect-v68',str(source),baseline)
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v67.json').read_bytes();old=json.loads(old_raw)
    if sha256(old_raw).hexdigest()!=PREVIOUS_SHA:raise ValueError('Prior contract changed')
    current=json.loads(old_raw);current.update(contract_version=68,previous_contract_sha256=PREVIOUS_SHA)
    directions={
        'TEST-HARNESS':"Within PreparedAssetsAreInspectable only, replace the private-static-font requirement with meaningful checks that actual instantiated prepared controls have usable instance font references. The source architecture prohibits unmanaged static state. Preserve every scene/control/catalog readiness assertion. Investigate the current AreSame null/null clone failure: Unity Object null wrappers must be checked with Unity-aware null semantics for deliberately absent vehicle-none references, while non-null asset reference identity, GUID identity and clone/source isolation remain tested. Never create runtime behavior, fake assets or mutate source assets to satisfy this readiness test.",
        'TEST-PRES-CORE':"Within Story_L1_05 only, correct Start's contradictory requirement: sufficient balance and Start must queue the currently selected tier under US-L9-05, without cycling that tier. Assert matching state and selected-tier preservation using actual service state. Preserve every existing bottom-button geometry, hit shape, Chat and Invite/partners navigation check. Tier changes remain covered independently; do not replace real interaction with DTO arrangement after clicking.",
        'TEST-PRES-NFR':"Within Story_NFR_03 only, replace the exact raw-only marquee assertion with substantive checks for the latest delivered message own-42 AND its actual author display name, as required by US-L1-04. Preserve all other read/unread, account isolation, event aggregation, conversation and pending-request assertions. Do not special-case message content in runtime code.",
    }
    for unit in current['units']:
        if unit['id'] in SCOPE:
            paths=author_paths(unit['id']);guid=sha256(paths[1].encode()).hexdigest()[:32]
            unit['owns']+=list(paths[1:])
            unit['instructions']+='\nCYCLE 68 EXPLICIT USER-APPROVED ACCEPTANCE RECONCILIATION. This supersedes contradictory historical assertions, not the approved requirements. '+directions[unit['id']]+' Change no other method body, helper, using, signature, attribute or source byte. Write '+paths[1]+' with the exact assertions corrected, source rationale, retained coverage and any remaining blocker; write '+paths[2]+' exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Every older owned note and metadata file remains frozen. These changes require actual independent review and fresh Red before implementation.'
        elif unit['role']=='impl':
            unit['instructions']+='\nCycle 68 owned-scope clarification: deliver the complete implementation within YOUR owned files, retaining prior paid workflows and repairing applicable actual failures. A complete proposal does not require modifying peer-owned or protected files. Report peer-owned defects accurately and allow the declared owners to repair them; do not withhold your entire owned implementation merely because shared verification needs peers. The independent Judge and full shared verification remain mandatory. All tests are read-only during implementation, including the newly approved authoring corrections after their new freeze.'
    validate_revision(old,current)
    (spec/'contract.v68.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    rules=UnityAdapter();contracts=[]
    for number in range(1,69):
        contracts.append(load_contract((spec/('contract.v'+str(number)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=160))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    check_frozen_sources(source,frozen)
    git(source,'add','specs/monopoly-game-lobby/contract.v68.json')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare approved method-bounded acceptance reconciliation')
    # Preserve the last full SHELL proposal and latest peer proposals verbatim.
    git(module,'worktree','add','-b','codex/lobby-paid-reference-v68',str(reference),candidate)
    shell=next(u for u in old['units'] if u['id']=='SHELL')
    shell_candidate='b53644293a4b41c3d1253e32acb5334781fcaeab'
    for path in shell['owns']:(reference/path).write_bytes(git(module,'show',shell_candidate+':'+path))
    git(reference,'add','--',*shell['owns'])
    git(reference,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Retain full paid owner proposals as read-only repair reference')
    retained_candidate=git(reference,'rev-parse','HEAD').decode().strip()
    owned={u.id:list(u.owns) for u in contract.units if u.role=='impl' and u.status=='active'}
    for unit,paths in owned.items():
        original=shell_candidate if unit=='SHELL' else candidate
        for path in paths:
            if git(module,'show',retained_candidate+':'+path)!=git(module,'show',original+':'+path):
                raise ValueError('Paid implementation provenance changed')
    protected={p:h for p,h in frozen.items() if p not in {item['path'] for item in SCOPE.values()}}
    manifest={'kind':'approved_test_reconciliation','version':68,'previous_services_sha256':sha256(prior_raw).hexdigest(),
        'previous_result_sha256':sha256(result_raw).hexdigest(),'dossier_sha256':sha256(dossier_raw).hexdigest(),
        'frozen':frozen,'judge_receipt_sha256':sha256(receipt_raw).hexdigest(),'scope':SCOPE,'human_accepted':False}
    restoration={'state':'complete','baseline':baseline,'retained_candidate':retained_candidate,'owned':owned,'tests':protected,
        'retained_proposals':{u:{p:sha256(git(module,'show',retained_candidate+':'+p)).hexdigest() for p in paths} for u,paths in owned.items()},
        'previous_evidence':json.loads((run/'services-v67/evidence/v67-step6-verify.json').read_bytes()),
        'note':'Current runtime is the exact proven pre-Green baseline for fresh Red. Reapply and repair the complete paid implementation for YOUR OWN files supplied read-only. SHELL reference comes from its last full paid proposal in cycle 66; peers come from cycle 67. Preserve their full workflows and current repairs. Corrected cycle-68 tests follow approved source requirements. Shared peer failures do not authorize editing peers or withholding all owned implementation. Every test is frozen before coding; Judge and complete verification remain mandatory.'}
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    for name,digest in {'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
                        'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}.items():
        if sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:raise ValueError('Trusted overlay changed')
    def reconciled() -> bool:
        check_frozen_sources(prior_integration,frozen);check_frozen_sources(source,frozen)
        return (json.loads((run/'services-v67/effects/transaction.json').read_bytes())['complete'] is True
            and not git(source,'status','--porcelain') and len(retained_run_reservations(state,budget._read()))==25)
    lease=RunLease(state,'monopoly-game-lobby','test-reconciliation-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'model-authorizations/test-reconciliation-v68.json',json.dumps(approval,indent=2).encode())
        atomic_write(state,'frozen-continuations/v68.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v68.json',json.dumps(restoration,indent=2).encode())
        active={'version':68,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v68','contract_sha256':contract.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        after=budget._read()
        if any(after['calls'].get(k)!=v for k,v in before['calls'].items()):raise ValueError('Accounting changed')
        print(json.dumps(active|{'usage':budget.totals(),'limits':budget.limits,'retained_candidate':retained_candidate,
            'previous_frozen_files':len(frozen),'still_carried_frozen':len(protected),'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
