"""Reconcile an incoherent mixed Red baseline with exact prior runtime blobs."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unity_coder.core.ownership import portable_path
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git,WorkspaceCandidate
if TYPE_CHECKING:
    from unity_coder.core.contracts import Contract
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.local_executor import LocalExecutionServices
    from lobby_production_host import ContextWorkers


def restoration_changes(owned: dict[str,list[str]],blobs: dict[str,bytes],tests: dict[str,str]) -> dict[str,dict[str,bytes]]:
    result={}
    for unit,paths in owned.items():
        result[unit]={}
        for path in paths:
            portable_path(path)
            if not path.startswith('Runtime/Script/') or path in tests or path not in blobs:
                raise ValueError('Restoration must use exact owned runtime blobs, never tests')
            result[unit][path]=blobs[path]
    return result


def positive_review(receipt: dict,sdk: dict,charge: dict,explanation: str) -> str:
    reply=receipt['reply'];decision=json.loads(reply['text'])
    if (decision.get('valid') is not True or decision.get('explanation')!=explanation
        or receipt['identity']['model']!='gpt-6.1-sol' or receipt['identity']['effort']!='medium'
        or reply['model']!='gpt-6.1-sol' or sdk['text']!=reply['text']
        or [sdk['input_tokens'],sdk['output_tokens']]!=charge.get('actual')
        or [reply['input_tokens'],reply['output_tokens']]!=charge.get('actual')):
        raise ValueError('A genuine settled positive independent source review is required')
    return explanation


def descriptor(state: Path,version: int) -> dict | None:
    path=state/'baseline-restorations'/('v'+str(version)+'.json')
    return json.loads(path.read_bytes()) if path.exists() else None


def extra_protection(state: Path,version: int) -> tuple[str,...]:
    value=descriptor(state,version)
    return tuple(value['tests']) if value else ()


def context(state: Path,module: Path,version: int) -> tuple[dict[str,dict[str,str]],str]:
    value=descriptor(state,version)
    if not value or value['state']!='complete':return {},''
    result={}
    for unit,files in value['retained_proposals'].items():
        body={}
        for path,digest in files.items():
            raw=git(module,'show',value['retained_candidate']+':'+path)
            if sha256(raw).hexdigest()!=digest:raise ValueError('Retained model proposal changed')
            body['readonly-retained-proposal/'+path]=raw.decode('utf-8')
        body['readonly-retained-proposal/provenance.json']=json.dumps({
            'retained_candidate':value['retained_candidate'],'restored_baseline':value['baseline'],
            'current_owned_files_are_proven_baseline_stubs':True,'all_tests_unchanged':True})
        result[unit]=body
    note=('\nBASELINE RESTORATION FACT: all implementation owners were restored to their exact proven pre-Green '
        'runtime snapshots because the mixed baseline contained runtime errors. Your full prior PAID model '
        'implementation is supplied under readonly-retained-proposal/. Reapply and repair that complete '
        'proposal into your owned files, preserving all workflows. The current stubs do not mean the prior '
        'work was discarded. Keep every test/configuration file unchanged. SHELL must also repair the three '
        'supplied async analyzer diagnostics while preserving cancellation and awaited completion semantics.')
    return result,note


def assert_tests(state: Path,version: int,integration: Path) -> None:
    value=descriptor(state,version)
    if not value:return
    from frozen_budget_continuation import check_frozen_sources
    check_frozen_sources(integration,value['tests'])


def restore(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
            integration: Path,workers: ContextWorkers) -> bool:
    from frozen_budget_continuation import check_frozen_sources
    from operational_transport import retained_run_reservations
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    evidence_raw=(run/'services-v66/evidence/v66-step2-red.json').read_bytes();evidence=json.loads(evidence_raw)
    if (contract.contract_version!=66 or contract.sha256!='65061cc3537f2d22830aaf77f698799427efd846c4724824be5039040699251b'
        or result['outcome']!='operational' or result['candidate_revision']!='aef0c6b67524943ccb96c212b9be0e7eff69fc4a'
        or services.tdd.frozen or evidence['gate']!='tests' or evidence['test_result']['failure_kind']!='setup'
        or len(evidence['test_result']['executed'])!=126):raise ValueError('Exact mixed baseline operational stop required')
    if len(retained_run_reservations(state,budget._read()))!=23:raise ValueError('Uncertain reservations changed')
    path='baseline-restorations/v66.json';plan=descriptor(state,66)
    if plan is None:
        if git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain'):
            raise ValueError('Mixed baseline candidate changed')
        owned={u.id:list(u.owns) for u in contract.units if u.role=='impl'}
        tests={p:sha256((integration/p).read_bytes()).hexdigest() for u in contract.units if u.role=='test' for p in u.owns}
        for p in ('Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef','Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef.meta'):
            tests[p]=sha256((integration/p).read_bytes()).hexdigest()
        if len(tests)!=189:raise ValueError('All 189 approved test/configuration files must remain')
        approvals={};ledger=budget._read()
        for unit in (u for u in contract.units if u.role=='test'):
            op='v66-step1-prepare-review-'+unit.id
            effect=services.effects.read('review-v66-step1-prepare-'+unit.id)
            explanation=effect['result']['explanation'];key=sha256(op.encode()).hexdigest();paid=run/'model-calls'/(key+'.json')
            if not paid.exists():
                reuse=json.loads((state/'review-reuse'/(key+'.json')).read_bytes())
                if reuse['operation_id']!=op or reuse['unit_id']!=unit.id:raise ValueError('Source review reuse changed')
                op=reuse['actual_judge_call'];key=sha256(op.encode()).hexdigest();paid=run/'model-calls'/(key+'.json')
            raw=paid.read_bytes();receipt=json.loads(raw);sdk_raw=(state/'codex-receipts'/(key+'.json')).read_bytes();sdk=json.loads(sdk_raw)
            positive_review(receipt,sdk,ledger['calls'][op],explanation)
            if (sdk['policy_sha256']!=receipt['identity']['backend_policy_sha256']
                or receipt['identity']['role']!='judge' or receipt['identity']['provider']!='codex'
                or ledger['calls'][op]['unit']!=unit.id
                or receipt['reply']['response_id']!=sdk['thread_id']+'/'+sdk['turn_id']):
                raise ValueError('Independent source review policy or unit identity changed')
            approvals[unit.id]={'explanation':explanation,'actual_judge_call':op,
                'receipt_sha256':sha256(raw).hexdigest(),'sdk_sha256':sha256(sdk_raw).hexdigest(),
                'preparation_attempts':services.tdd.state(unit.id).preparation_attempts}
        retained='651c60ac70136310b7bc3fda7d17efd9464b1784';baseline='02460607473eb7be1cb5919f3daa1de160c92d0d'
        proposals={u:{p:sha256(git(services.manager.repository,'show',retained+':'+p)).hexdigest() for p in paths} for u,paths in owned.items()}
        plan={'state':'pending','before':result['candidate_revision'],'contract_sha256':contract.sha256,
            'baseline':baseline,'retained_candidate':retained,'owned':owned,'tests':tests,'source_approvals':approvals,
            'retained_proposals':proposals,'evidence_sha256':sha256(evidence_raw).hexdigest(),'usage':budget.totals(),
            'human_accepted':False}
        atomic_write(state,path,json.dumps(plan,indent=2).encode())
    if plan['evidence_sha256']!=sha256(evidence_raw).hexdigest():raise ValueError('Original mixed evidence changed')
    check_frozen_sources(integration,plan['tests'])
    if plan['state']=='pending':
        tx=services.effects.read('transaction')
        if tx['operation']!='baseline-restoration-v66':
            if not tx['complete'] or tx['operation']!='v66-step3-prepare':raise ValueError('Unexpected active transaction')
            services.effects.write('transaction',{'stage':'prepare','operation':'baseline-restoration-v66',
                'checkpoint':services._save(),'complete':False})
        blobs={p:git(services.manager.repository,'show',plan['baseline']+':'+p) for paths in plan['owned'].values() for p in paths}
        changes=restoration_changes(plan['owned'],blobs,plan['tests'])
        for unit,desired in changes.items():
            name='full-baseline-v66-'+unit;prior=services.effects.read('apply-'+name)
            base=prior['identity']['base'] if prior else git(integration,'rev-parse','HEAD').decode().strip()
            delta={p:raw for p,raw in desired.items() if git(integration,'show',base+':'+p)!=raw}
            if delta:services.effects.apply(name,WorkspaceCandidate(unit,contract.sha256,base,{},delta))
        for unit,fact in plan['source_approvals'].items():
            if services.tdd.state(unit).preparation_attempts!=fact['preparation_attempts']:raise ValueError('Actual preparation count changed')
            services.tdd.approve_tests(unit,fact['explanation'])
        check_frozen_sources(integration,plan['tests']);services._save()
        services.effects.write('transaction',{'stage':'prepare','operation':'baseline-restoration-v66','complete':True,'checkpoint':services._save()})
        plan.update(state='complete',after=git(integration,'rev-parse','HEAD').decode().strip())
        atomic_write(state,path,json.dumps(plan,indent=2).encode())
    if git(integration,'rev-parse','HEAD').decode().strip()!=plan['after']:raise ValueError('Restored baseline head changed')
    additions,note=context(state,services.manager.repository,66)
    for unit,files in additions.items():workers.supplemental_context.setdefault(unit,{}).update(files)
    workers.restored_baseline_note=note
    workers.carried_tests=tuple(plan['tests'])
    services.manager.frozen_paths=tuple(dict.fromkeys(services.manager.frozen_paths+tuple(plan['tests'])))
    return True
