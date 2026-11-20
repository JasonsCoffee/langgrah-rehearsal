"""Add one independently requested test in new files; retain all frozen tests."""
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid5,NAMESPACE_URL
from supplemental_frozen_coverage import validate_supplement
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
    if (result['outcome']!='rework' or result['contract_version']!=65
        or result['candidate_revision']!='36cdcd196d5024844066814f81c429fabc4ac898'
        or result['contract_sha256']!='edddecafb90f10bfab23e7aadeac2640bf57582a3e04c1e5e376975305b54e5b'):
        raise ValueError('Exact frozen-review rework required')
    old_carry_raw=(state/'frozen-continuations/v65.json').read_bytes();old_carry=json.loads(old_carry_raw);frozen=old_carry['frozen']
    prior_raw=(run/'services-v65/state.json').read_bytes();prior=json.loads(prior_raw)
    if prior['tdd']['states']['TEST-PARTNER-RECS']['preparation_attempts']!=1:raise ValueError('Real source-review count changed')
    call='v65-step1-prepare-review-TEST-PARTNER-RECS';key=sha256(call.encode()).hexdigest()
    review_ref='.agent/runs/monopoly-game-lobby/model-calls/'+key+'.json';review_raw=(state/review_ref).read_bytes()
    review=json.loads(review_raw);negative=json.loads(review['reply']['text'])
    if negative['valid'] is not False or review['reply']['model']!='gpt-6.1-sol':raise ValueError('Actual independent negative review required')
    dossier_raw=(run/'dossier-v65.json').read_bytes()
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    if budget.limits!=[125000000,12000000,80,2] or len(retained_run_reservations(state,budget._read()))!=23:
        raise ValueError('Budget or retained reservations changed')
    source=root/'worktrees/architect-v66'
    if source.exists():raise ValueError('Preserve existing supplementary preparation')
    git(module,'worktree','add','-b','codex/lobby-architect-v66',str(source),result['candidate_revision'])
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v65.json').read_bytes();old=json.loads(old_raw)
    current=json.loads(old_raw);current.update(contract_version=66,previous_contract_sha256=sha256(old_raw).hexdigest())
    author='TEST-PARTNER-RECS';source_test='jj.Monopoly.Tests.LobbyRehearsal.LobbySocialTests.Story_L4_13'
    new_test='jj.Monopoly.Tests.LobbyRehearsal.LobbySocialTests.Story_L4_13_OriginPriority'
    cs='Tests/Runtime/Script/LobbyRehearsal/LobbySocialPartnerPriorityTests.cs'
    note=cs.removesuffix('.cs')+'.coverage-v66.md';paths=[cs,cs+'.meta',note,note+'.meta']
    if any((source/p).exists() for p in paths):raise ValueError('Supplementary file name is already used')
    source_link=next(t for t in old['test_links'] if t['test_id']==source_test)
    implementers=list(dict.fromkeys(source_link['implementing_units']+['RECORDS']))
    current['test_links'].append(source_link|{'test_id':new_test,'implementing_units':implementers})
    target=next(u for u in current['units'] if u['id']==author);target['owns']+=paths;target['acceptance'].append(new_test)
    guids={p:uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+p).hex for p in (cs,note)}
    target['instructions']=(
        'All original test files, helpers, notes and maps are globally frozen and READ-ONLY. Author ONLY the four new supplemental files listed below; preserve every old byte. '
        'Add the single enabled async NUnit test '+new_test+' in '+cs+', as another public sealed partial class LobbySocialTests in namespace jj.Monopoly.Tests.LobbyRehearsal. '
        'Use the supplied real SocialFixture/private helpers from the unchanged partial files and genuine service/UI stimuli; do not fabricate business outcomes. '
        'The actual independent Judge rejected the older coverage for this reason: '+negative['explanation']+' '
        'The new test must independently refute a newest-origin-only implementation. Use the same account with an OLDER pending cooperation/friend request and NEWER partner AND rival history; require exactly one actual rendered row with cooperation origin. '
        'Then remove the request through the real service and require an OLDER partner history to win over NEWER rival history, again exactly one rendered row, with the correct origin labels and forbidden lower-priority origins absent. '
        'Assert the crossed timestamp relationships explicitly. Keep row-observation guards before dereferencing UI objects so nonfunctional baseline fails by assertion. No ignores, no swallowed exceptions, no handcrafted recommendation/priority business logic. '
        'Existing Story_L4_13 and all of its assertions remain unchanged. The new test supplements its origin-priority clause; it does not replace any old test. '
        'Write '+note+' mapping this supplementary case to US-L4-13 and explaining the counterexample and preserved older coverage truthfully, with no claim of execution or human acceptance. '
        'Also write '+cs+'.meta and '+note+'.meta with fileFormatVersion: 2 and exact guid values '+guids[cs]+' and '+guids[note]+' respectively. '
        'Return strict JSON files/reason, complete contents for only these new files. Original files are provided solely as read-only context.')
    for unit in current['units']:
        if unit['id'] in implementers:unit['acceptance'].append(new_test)
    validate_supplement(old,current,sha256(old_raw).hexdigest(),author,paths,new_test,source_test,implementers=implementers)
    (spec/'contract.v66.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    rules=UnityAdapter();contracts=[]
    for n in range(1,67):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=80))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',
        implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    check_frozen_sources(source,frozen)
    git(source,'add','specs/monopoly-game-lobby/contract.v66.json')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Add new priority-counterexample test scope while retaining every frozen assertion')
    manifest={k:old_carry[k] for k in ('retained_candidate','retained_proposal_files','compiler_diagnostics')}
    manifest.update(kind='supplemental_frozen_coverage',version=66,frozen=frozen,previous_services_sha256=sha256(prior_raw).hexdigest(),
        previous_result_sha256=sha256(result_raw).hexdigest(),dossier_sha256=sha256(dossier_raw).hexdigest(),
        previous_carry_sha256=sha256(old_carry_raw).hexdigest(),negative_review_ref=review_ref,negative_review_sha256=sha256(review_raw).hexdigest(),
        author_unit=author,new_paths=paths,supplementary_test=new_test,source_test=source_test,implementing_units=implementers,
        reason='Actual negative review requires crossed timestamps. New files only; all 185 original frozen files are unchanged. RECORDS owns the recommendation service used by this new case.',human_accepted=False)
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    def reconciled() -> bool:
        retained_run_reservations(state,budget._read());check_frozen_sources(source,frozen)
        return (state/'frozen-review-routing/v65/receipt.json').exists() and not git(source,'status','--porcelain')
    lease=RunLease(state,'monopoly-game-lobby','supplemental-coverage-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'frozen-continuations/v66.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,workers_reconciled=reconciled)
        active={'version':66,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v66','contract_sha256':contract.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'usage':budget.totals(),'limits':budget.limits,'preserved_frozen_files':len(frozen),
            'new_authoring_paths':paths,'selected_tests':len(current['test_links']),'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
