"""Consecutive append-only coverage and paid-proposal repair after real rework."""
from hashlib import sha256
import json
import os
from pathlib import Path
from actual_judge_feedback import validate_finding
from frozen_budget_continuation import check_frozen_sources
from operational_transport import retained_run_reservations
from reviewed_source_supplement import validate_append
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
    state=root/'trusted-state';module=root/'module';run=state/'.agent/runs/monopoly-game-lobby'
    result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    expected='a3c9baa004dabeb77eec0b233ee03d18deb3dc45a31e90134356c4a4748b736e'
    candidate='830e171a6838ab07961d385bdc4be47b6a162ce5'
    if (result['outcome']!='rework' or result['contract_version']!=68
        or result['contract_sha256']!=expected or result['candidate_revision']!=candidate):
        raise ValueError('Only the actual unchanged-candidate cycle-68 rework may advance')
    dossier_raw=(run/'dossier-v68.json').read_bytes();dossier=json.loads(dossier_raw)
    if not any(u['id']=='SHELL' and u['defect_class']=='contract' for u in dossier['failed_units']):
        raise ValueError('Native bounded-repair escalation is required')
    current=root/'worktrees/monopoly-game-lobby/integration-v68'
    prior=json.loads((run/'services-v68/state.json').read_bytes());frozen=prior['tdd']['frozen']
    if len(frozen)!=195 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!='28fec4be892147775c869eb39ebf8e9a899ed869e3602f0606f950c44db06800':
        raise ValueError('Complete approved frozen test inventory changed')
    check_frozen_sources(current,frozen)
    if git(current,'rev-parse','HEAD').decode().strip()!=candidate or git(current,'status','--porcelain'):
        raise ValueError('Previous source candidate changed')
    evidence_raw=(run/'services-v68/evidence/v68-step11-verify.json').read_bytes();evidence=json.loads(evidence_raw)
    if evidence['gate']!='compile' or evidence['status']!='failed' or evidence['request']['candidate_revision']!=candidate:
        raise ValueError('Actual unchanged-candidate compile evidence required')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=250000000,output_limit=24000000,max_cycles=160,max_added_units=2)
    ledger=budget._read()
    if len(retained_run_reservations(state,ledger))!=25:raise ValueError('Uncertain reservations changed')
    operation=evidence['request']['request_id'];call=operation+'-judge-SHELL';key=sha256(call.encode()).hexdigest()
    effect=json.loads((run/('services-v68/effects/judge-'+operation+'-SHELL.json')).read_bytes())
    receipt=json.loads((run/'model-calls'/(key+'.json')).read_bytes());sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
    finding=validate_finding(evidence['request'],effect,receipt,sdk,ledger['calls'][call],'SHELL')
    negative_call='v68-step2-prepare-review-TEST-RECORDS';negative_key=sha256(negative_call.encode()).hexdigest()
    negative_ref='.agent/runs/monopoly-game-lobby/model-calls/'+negative_key+'.json'
    negative_raw=(state/negative_ref).read_bytes();negative=json.loads(negative_raw)
    if json.loads(negative['reply']['text'])['valid'] is not False:raise ValueError('Actual visibility coverage rejection required')
    source=root/'worktrees/architect-v69'
    if source.exists():raise ValueError('Preserve existing preparation and reconcile explicitly')
    git(module,'worktree','add','-b','codex/lobby-architect-v69',str(source),candidate)
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v68.json').read_bytes();old=json.loads(old_raw)
    new=json.loads(old_raw);new.update(contract_version=69,previous_contract_sha256=sha256(old_raw).hexdigest())
    author='TEST-RECORDS';prefix='Tests/Runtime/Script/LobbyRehearsal/'
    paths=[prefix+'LobbyRecordsVisibilityTests.cs',prefix+'LobbyRecordsVisibilityTests.cs.meta',
           prefix+'LobbyRecordsVisibility.acceptance.md',prefix+'LobbyRecordsVisibility.acceptance.md.meta']
    cases=[('Story_L5_01','RankingTabCaptionsRendered'),('Story_L5_11','JournalEntriesRenderedWithinViewport'),
           ('Story_L6_04','ExpandedHistoryDetailsVisibleWithinViewport')]
    links=[]
    for original,name in cases:
        link=next(t for t in old['test_links'] if t['test_id']=='jj.Monopoly.Tests.LobbyRehearsal.LobbyRecordsSettingsTests.'+original)
        links.append(link|{'test_id':'jj.Monopoly.Tests.LobbyRehearsal.LobbyRecordsVisibilityTests.'+name})
    for unit in new['units']:
        additions=[l['test_id'] for l in links if unit['id']==author or unit['id'] in l['implementing_units']]
        if additions:unit['acceptance']+=additions
        if unit['id']==author:
            unit['owns']+=paths
            unit['instructions']+='\nCYCLE 69 FINAL APPEND-ONLY COVERAGE OVERRIDE: every existing test, helper, note and metadata file is frozen. Do not rewrite or duplicate any of the old 24 methods. Implement ONLY the three new enabled NUnit tests in class jj.Monopoly.Tests.LobbyRehearsal.LobbyRecordsVisibilityTests: RankingTabCaptionsRendered, JournalEntriesRenderedWithinViewport, ExpandedHistoryDetailsVisibleWithinViewport. Reuse the actual read-only LobbyHarness and supplied ports. Verify the documented Chinese day/week captions as rendered text and actual tab navigation. Publish distinct journal entries through the real fake records service, open the real Records view, expand a real row and prove each persisted entry ID/source/amount has visible, nontransparent glyphs within the actual detail viewport and ancestor clipping bounds; stored or parsed text alone is insufficient. For history, prove newest-first rows and expanded income/expense glyphs really occupy the viewport; prove collapse removes the displayed detail and reopening restores it. Include effective inherited CanvasGroup alpha and real clipping geometry in observations. Do not implement business behavior, arrange expected UI state directly, skip missing controls or accept off-screen ordering as visibility. Old substantive assertions remain unchanged; these are supplementary cases. Implement only the new file and new truthful coverage map; all four new paths are exclusive. Expected failures against stubs are valid Red. '
            for path in paths:
                if path.endswith('.meta'):unit['instructions']+=' Write '+path+' exactly fileFormatVersion: 2 newline guid: '+sha256(path.encode()).hexdigest()[:32]+' newline.'
    new['test_links']+=links
    validate_append(old,new,sha256(old_raw).hexdigest(),author,paths,links)
    (spec/'contract.v69.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    # Restore exact, previously executed assertion-Red runtime blobs, never tests.
    baseline='4333140e62c550bd3fc0050d83b6abf24c89770e'
    owned={u['id']:list(u['owns']) for u in old['units'] if u['role']=='impl' and u['status']=='active'}
    for names in owned.values():
        for path in names:(source/path).write_bytes(git(module,'show',baseline+':'+path))
    check_frozen_sources(source,frozen)
    rules=UnityAdapter();contracts=[]
    for number in range(1,70):
        contracts.append(load_contract((spec/('contract.v'+str(number)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=160))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    git(source,'add','--','specs/monopoly-game-lobby/contract.v69.json',*(p for names in owned.values() for p in names))
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Preserve frozen coverage; append Records visibility tests and retain paid runtime repair')
    manifest={'kind':'reviewed_source_supplement','version':69,'author_unit':author,'new_paths':paths,'new_links':links,
        'source_revision':candidate,'frozen':frozen,'previous_result_sha256':sha256(result_raw).hexdigest(),
        'dossier_sha256':sha256(dossier_raw).hexdigest(),'negative_review_ref':negative_ref,
        'negative_review_sha256':sha256(negative_raw).hexdigest(),'negative_sdk_ref':'codex-receipts/'+negative_key+'.json',
        'human_accepted':False}
    note=('The runtime baseline was restored byte-for-byte only for fresh valid Red. Your COMPLETE latest paid implementation is supplied read-only. Reapply it and repair actual failures within your ownership; preserve every workflow and every frozen test. '
          'SHELL-specific verified toolchain constraint: JJCK0011 rejects the negated-is catch filter even though it logically excludes cancellation. The compiler diagnostic requires its supported is-not pattern form. The historical framework-context.md example uses the rejected older expression; it is not evidence that the active analyzer accepts it. The last repair returned no changes and the same candidate failed again. A no-op or reapplying the rejected filters is not a repair. Preserve cancellation propagation and async completion while making concrete owned-source changes. Preserve the now-correct generated lifecycle region inside OnDestroy. '+finding)
    restoration={'state':'complete','baseline':baseline,'retained_candidate':candidate,'owned':owned,'tests':frozen,
        'retained_proposals':{u:{p:sha256(git(module,'show',candidate+':'+p)).hexdigest() for p in names} for u,names in owned.items()},
        'previous_evidence':evidence,'independent_findings':{'SHELL':json.loads(receipt['reply']['text'])},'note':note}
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    def reconciled() -> bool:
        check_frozen_sources(current,frozen);check_frozen_sources(source,frozen)
        return (json.loads((run/'services-v68/effects/transaction.json').read_bytes())['complete'] is True
            and len(retained_run_reservations(state,budget._read()))==25 and not git(source,'status','--porcelain'))
    lease=RunLease(state,'monopoly-game-lobby','records-supplement-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'frozen-continuations/v69.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v69.json',json.dumps(restoration,indent=2).encode())
        active={'version':69,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v69','contract_sha256':contract.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        after=budget._read()
        if any(after['calls'].get(k)!=v for k,v in ledger['calls'].items()):raise ValueError('Usage history changed')
        print(json.dumps(active|{'usage':budget.totals(),'limits':budget.limits,'retained_candidate':candidate,
            'frozen_preserved':195,'new_cases':len(links),'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
