"""Opt-in real-model rehearsal using the existing frozen isolated fixture."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time
import run as demo
from unity_coder.core.ai_models import load_ai_config, ModelClient
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.model_calls import ModelCalls, JudgeInput, judge_prompt
from unity_coder.core.model_workers import parse_patch, parse_judgement


def main() -> None:
    run_id='real-model-'+demo.ATTEMPT
    os.environ['VERIFY_RUN_ID']=run_id
    settings=load_ai_config(Path('ai.local.toml'))
    baseline=json.loads((demo.ROOT/'baseline.json').read_bytes())
    frozen=json.loads((demo.ROOT/'freeze.json').read_bytes())
    rules=demo.UnityAdapter()
    contract=demo.load_contract((demo.REPO/'specs/demo/contract.v1.json').read_bytes(),demo.REPO,rules)
    manager=demo.WorkspaceManager(demo.REPO,demo.ROOT/'worktrees',contract,rules,run_id=run_id,
        imported_roots=(demo.HOST/'Assets',),frozen_paths=tuple(frozen))
    integration=manager.create_integration(1,baseline['commit'])
    units={u:manager.create_unit(u,baseline['commit'],{}) for u in ('A','B')}
    for handle in (integration,*units.values()):
        for path,expected in frozen.items():
            assert demo.digest((handle.path/path).read_bytes())==expected
    req,red=demo.verify(run_id+'-red',integration.path)
    assert set(red.failed)==set(demo.TESTS)
    tdd=demo.TDDCoordinator(contract,integration.path,rules,test_config_paths=tuple(frozen))
    tdd.approve_tests('T','Previously frozen fixture; five live assertion failures confirmed again. Test review is explicit fixture review, not an implementation-model approval.')
    for u in units: tdd.record_baseline(u,demo.BehaviorEvidence(req.candidate_revision,demo.TESTS,red))
    tdd.freeze()
    budget=BudgetLedger(demo.ROOT/'model-state',run_id,input_limit=100000,output_limit=32768,max_cycles=3,max_added_units=2)
    budget.begin_cycle(1,contract.sha256,{'A':('A',),'B':('B',)})
    coder=ModelCalls(ModelClient(settings.coder,timeout=60),budget,run_id)
    judge=ModelCalls(ModelClient(settings.judge,timeout=60),budget,run_id)
    spec=(demo.REPO/contract.spec.path).read_text()
    judgements={}
    for u in ('A','B'):
        unit=next(x for x in contract.units if x.id==u)
        context=JudgeInput('\n'.join(unit.acceptance),spec,
            {'gate':'tests','failed':[t for t in red.failed if t in unit.acceptance]},
            {p:x.id for x in contract.units for p in x.owns},
            {p:(integration.path/p).read_text() for p in (*demo.CODE,demo.TEST)})
        reply=judge.generate('judge-red-'+u,u,judge_prompt(context),max_output_tokens=2048)
        classification,explanation=parse_judgement(reply.text)
        judgements[u]={'defect_class':classification,'explanation':explanation}
        if classification!='implementation':
            raise ValueError('Judge routed fixture to contract rework; do not override')
    demo.emit(run_id+'-judge',judgements)
    timings={}
    def generate(unit):
        timings[unit.id]={'start':time.monotonic()}
        context={'spec':spec,'owns':unit.owns,'acceptance':unit.acceptance,
                 'files':{p:(integration.path/p).read_text() for p in (*demo.CODE,demo.TEST)}}
        prompt=('Implement only your owned files to satisfy the frozen tests. Preserve public APIs. '
                'Other components are implemented independently. Return ONLY JSON: '
                '{"files":{"owned/path":"complete source text"},"reason":"brief explanation"}. '
                'Never change tests, assembly definitions or metadata.\n'+json.dumps(context))
        reply=coder.generate('green-'+unit.id,unit.id,prompt,max_output_tokens=4096)
        patch,_=parse_patch(reply.text,unit.owns)
        host=demo.ExecutionHost(units[unit.id],contract,rules,frozen_paths=tuple(frozen))
        for p,content in patch.items(): host.write_file(p,content)
        timings[unit.id]['finish']=time.monotonic()
        return patch
    candidates=demo.dispatch_parallel(tdd,generate)
    if any(c.violation for c in candidates):
        raise ValueError('Model candidate rejected: '+str([c.violation for c in candidates]))
    for u in units:
        tdd.pending_shared(u)
        manager.integrate(integration,manager.capture(units[u]),{})
    req,green=demo.verify(run_id+'-green',integration.path)
    if green.failed: raise ValueError('Real candidate needs bounded repair; retained for diagnosis')
    tdd.record_group_green(('A','B'),demo.BehaviorEvidence(req.candidate_revision,demo.TESTS,green))
    green_commit=demo.git(integration.path,'rev-parse','HEAD').decode().strip()
    refactor_manager=demo.WorkspaceManager(demo.REPO,demo.ROOT/'worktrees',contract,rules,
        run_id=run_id+'-refactor',imported_roots=(demo.HOST/'Assets',),frozen_paths=tuple(frozen))
    refactored=[]
    for u in units:
        unit=next(x for x in contract.units if x.id==u)
        prompt=('Review this passing implementation for refactoring. Preserve all behavior and public APIs. '
                'Return ONLY JSON with files mapping owned paths to complete replacement text, and reason. '
                'If no improvement is warranted return an empty files object and explain why.\n'+
                json.dumps({'spec':spec,'owns':unit.owns,'files':{p:(integration.path/p).read_text() for p in unit.owns}}))
        reply=coder.generate('refactor-'+u,u,prompt,max_output_tokens=4096)
        patch,reason=parse_patch(reply.text,unit.owns)
        patch={p:v for p,v in patch.items() if (integration.path/p).read_bytes()!=v}
        if not patch:
            tdd.finish_refactor(u,reason=reason)
        else:
            tdd.begin_refactor(u)
            handle=refactor_manager.create_unit(u,green_commit,{})
            host=demo.ExecutionHost(handle,contract,rules,frozen_paths=tuple(frozen))
            for p,v in patch.items(): host.write_file(p,v)
            manager.integrate(integration,refactor_manager.capture(handle),{})
            refactored.append(u)
    req,confirmed=demo.verify(run_id+'-refactor',integration.path)
    if confirmed.failed: raise ValueError('Refactor needs bounded repair; candidate retained')
    for u in refactored:
        tdd.finish_refactor(u,demo.BehaviorEvidence(req.candidate_revision,demo.TESTS,confirmed))
    tdd.assert_frozen()
    for handle in (integration,*units.values()):
        for p,expected in frozen.items(): assert demo.digest((handle.path/p).read_bytes())==expected
    for p,expected in frozen.items(): assert demo.digest((demo.GAME/p).read_bytes())==expected
    demo.emit(run_id+'-summary',{'run_id':run_id,'coder':settings.coder.model,'judge':settings.judge.model,
        'judge_temperature_mode':settings.judge.temperature_mode,'judge_effort':settings.judge.effort,
        'judgements':judgements,'red_failed':len(red.failed),'green_passed':len(green.passed),
        'refactor_passed':len(confirmed.passed),'timings':timings,'usage':budget.totals(),
        'stages':{u:tdd.state(u).stage for u in units},'frozen_inputs_preserved':True,
        'integration_commit':demo.git(integration.path,'rev-parse','HEAD').decode().strip(),
        'snapshot':req.candidate_revision,'human_accepted':False,'exported_graph_exercised':False})
    print('Real-model isolated rehearsal complete',flush=True)


if __name__=='__main__': main()
