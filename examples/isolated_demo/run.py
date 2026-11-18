"""Explicit opt-in live demo; use DEMO_ROOT and UNITY_HOST machine selectors.

This is a deterministic component demonstration, not the production graph or
model/judge acceptance. It never alters existing game test selections or files.
"""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid5, NAMESPACE_URL
from threading import Barrier

from unity_coder.adapters.unity.transport import BridgeTransport, local_http
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.contracts import load_contract
from unity_coder.core.workspaces import git
from unity_coder.core.verification import VerificationRequest
from unity_coder.core.verification import VerificationResult
from unity_coder.core.workspaces import WorkspaceManager
from unity_coder.core.execution_host import ExecutionHost
from unity_coder.core.tdd import TDDCoordinator, BehaviorEvidence
from unity_coder.core.evidence import TestResult
from unity_coder.core.dispatch import dispatch_parallel
from unity_coder.core.integration import shared_failure

ROOT = Path(os.environ['DEMO_ROOT']).resolve()
HOST = Path(os.environ['UNITY_HOST']).resolve()
GAME = HOST / 'Assets/JJGame/monopoly'
PORT = int(os.environ.get('UNITY_BRIDGE_PORT', '49166'))
ATTEMPT = os.environ.get('DEMO_ATTEMPT', '1')
PREFIX = 'Editor/Script/FrameworkDemo'
REPO = ROOT / 'module'
NAMES = ('CreditsAreAdded', 'NegativeCreditsAreIgnored', 'ScoresAreAdded', 'ScoresAreCapped', 'SharedRewardUsesBothComponents')
TESTS = tuple('FrameworkDemo.Tests.Acceptance.' + name for name in NAMES)
CODE = (PREFIX + '/Code/CreditCalculator.cs', PREFIX + '/Code/ScoreCalculator.cs')
TEST = PREFIX + '/Tests/FrameworkDemoTests.cs'

def digest(content: bytes) -> str:
    return sha256(content).hexdigest()

def write(root: Path, path: str, data: bytes) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

def emit(name: str, data: object) -> None:
    write(ROOT, name + '.json', json.dumps(data, indent=2).encode())

def refresh() -> None:
    health = local_http(PORT, 'GET', '/', None, 5)
    if Path(health['projectPath']).resolve() != HOST:
        raise ValueError('Wrong live host')
    reply = local_http(PORT, 'POST', '/execute', {'command':'RefreshAssetDatabase'}, 10)
    ticket = reply.get('taskId')
    idle = 0
    for _ in range(60):
        time.sleep(1)
        try:
            if ticket:
                result = local_http(PORT, 'GET', '/task/' + ticket, None, 3)
                if result.get('status') == 'error' and 'not found' not in str(result):
                    raise ValueError(str(result))
            # Capabilities execute on the editor thread after reload.
            result = local_http(PORT, 'POST', '/execute', {'command':'FrameworkVerifyCapabilities'}, 3)
            data=json.loads(result.get('data','{}'))
            if result.get('status') == 'success' and data.get('ready') is True and not data.get('active_ticket'):
                idle += 1
                if idle >= 3:
                    return
            else:
                idle = 0
        except (OSError, json.JSONDecodeError):
            idle = 0
            continue
    raise TimeoutError('Editor refresh did not settle')

def snapshot(source: Path) -> str:
    files = {p.relative_to(source).as_posix(): digest(p.read_bytes())
             for p in (source / PREFIX).rglob('*') if p.is_file()}
    return digest(json.dumps(files, sort_keys=True).encode())

def verify(label: str, source: Path, selection: tuple[str, ...] = TESTS):
    contract = load_contract((REPO/'specs/demo/contract.v1.json').read_bytes(), REPO, UnityAdapter())
    for path in (source/PREFIX).rglob('*'):
        if path.is_file():
            relative=path.relative_to(source).as_posix()
            if not (GAME/relative).exists() or (GAME/relative).read_bytes()!=path.read_bytes():
                write(GAME, relative, path.read_bytes())
    refresh()
    # Import-created metadata becomes part of the snapshot before verification.
    for path in (GAME/PREFIX).rglob('*.meta'):
        relative = path.relative_to(GAME).as_posix()
        if not (source/relative).exists():
            write(source, relative, path.read_bytes())
    identity = snapshot(source)
    request = VerificationRequest('isolated-' + ATTEMPT + '-' + label, os.environ.get('VERIFY_RUN_ID','isolated-demo'), 1, contract.sha256,
        identity, contract.presentation_ref.sha256, contract.coding_profile_ref.sha256,
        contract.environment_ref.sha256, selection, selection == TESTS)
    worker = BridgeTransport(HOST, ports=(PORT,), timeout=180)
    compiled = worker.compile(request)
    emit(label + '-compile', asdict(compiled))
    if compiled.compilation.operational_error or not compiled.compilation.passed:
        raise ValueError('Demo compilation failed: ' + str(compiled))
    result = worker.run_tests(request)
    emit(label, asdict(result))
    if result.tests.operational_error:
        raise ValueError(result.tests.operational_error)
    if snapshot(GAME) != identity:
        raise ValueError('Demo changed during verification')
    print(label, 'passed', len(result.tests.passed), 'failed', len(result.tests.failed), flush=True)
    return request, result.tests

def prepare() -> None:
    if REPO.exists() or (GAME/PREFIX).exists():
        raise ValueError('Demo destination already exists; no implicit overwrite')
    REPO.mkdir(parents=True)
    git(REPO, 'init', '-b', 'codex/demo-baseline')
    git(REPO, 'config', 'user.name', 'Framework isolated demo')
    git(REPO, 'config', 'user.email', 'demo@example.invalid')
    git(REPO, 'config', 'core.autocrlf', 'false')
    for path, name in zip(CODE, ('CreditCalculator', 'ScoreCalculator')):
        write(REPO, path, f'namespace FrameworkDemo {{ public sealed class {name} {{ public int Calculate(int current, int amount) => 0; }} }}\n'.encode())
    write(REPO, TEST, Path('examples/isolated_demo/FrameworkDemoTests.cs').read_bytes())
    write(REPO, PREFIX+'/Code/Framework.Demo.Code.asmdef', json.dumps({'name':'Framework.Demo.Code','includePlatforms':['Editor']}).encode())
    write(REPO, PREFIX+'/Tests/Framework.Demo.Tests.asmdef', json.dumps({'name':'Framework.Demo.Tests','references':['Framework.Demo.Code'], 'includePlatforms':['Editor'],'optionalUnityReferences':['TestAssemblies']}).encode())
    for path in list((REPO/PREFIX).rglob('*')):
        if path.is_file():
            relative = path.relative_to(REPO).as_posix()
            write(REPO, relative+'.meta', ('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL, 'isolated-demo/'+relative).hex+'\n').encode())
    spec = 'specs/demo/spec.md'
    write(REPO, spec, b'DEMO: add positive credits; cap scores at 100; shared reward sums both. Editor-only diagnostic. No game acceptance claim.')
    data = dict(format_version=1, contract_version=1, module='isolated-demo', module_root=PREFIX+'/Code', test_roots=[PREFIX+'/Tests'], spec_ref=spec, spec_sha256=digest((REPO/spec).read_bytes()), ownership_migrations=[])
    for field in ('presentation_ref','coding_profile_ref','environment_ref'):
        path='specs/demo/'+field+'.json'
        content=json.dumps({'purpose':'isolated Editor-only diagnostic','package_lock':digest((HOST/'Packages/packages-lock.json').read_bytes())}).encode()
        write(REPO,path,content);data[field]={'path':path,'sha256':digest(content)}
    data['units']=[]
    for id,role,owns,acceptance in [('T','test',[TEST],TESTS),('A','impl',[CODE[0]],(TESTS[0],TESTS[1],TESTS[4])),('B','impl',[CODE[1]],(TESTS[2],TESTS[3],TESTS[4]))]:
        data['units'].append(dict(id=id,role=role,status='active',title=id,spec_ref='DEMO',owns=owns,acceptance=list(acceptance),depends_on=[],interfaces=[],instructions='Isolated deterministic fixture; preserve frozen tests.'))
    data['test_links']=[dict(test_id=t,author_unit='T',implementing_units=['A','B'] if i==4 else ['A' if i<2 else 'B'],criterion='DEMO') for i,t in enumerate(TESTS)]
    data['task_links']=[dict(task_ref='demo:1',unit_ids=['T','A','B'],criteria=['DEMO'])]
    write(REPO,'specs/demo/contract.v1.json',json.dumps(data,indent=2).encode())
    freeze_red()

def freeze_red() -> None:
    request,result=verify('red-corrected',REPO)
    if set(result.failed)!=set(TESTS) or result.skipped or result.inconclusive:
        raise ValueError('Expected five behavioral Red failures')
    emit('freeze', {p.relative_to(REPO).as_posix():digest(p.read_bytes()) for p in (REPO/PREFIX).rglob('*') if p.is_file() and ('/Tests/' in p.as_posix() or p.suffix in ('.asmdef','.meta'))})
    git(REPO,'add','.')
    git(REPO,'commit','-m','Freeze isolated demo tests after live Red')
    emit('baseline',{'commit':git(REPO,'rev-parse','HEAD').decode().strip(),'snapshot':request.candidate_revision})

def demonstrate() -> None:
    baseline=json.loads((ROOT/'baseline.json').read_bytes())
    frozen=json.loads((ROOT/'freeze.json').read_bytes())
    rules=UnityAdapter()
    contract=load_contract((REPO/'specs/demo/contract.v1.json').read_bytes(),REPO,rules)
    manager=WorkspaceManager(REPO,ROOT/'worktrees',contract,rules,run_id='isolated-demo-'+ATTEMPT,
                             imported_roots=(HOST/'Assets',),frozen_paths=tuple(frozen))
    integration=manager.create_integration(1,baseline['commit'])
    units={id:manager.create_unit(id,baseline['commit'],{}) for id in ('A','B')}
    for handle in (integration, *units.values()):
        for path, expected in frozen.items():
            if digest((handle.path/path).read_bytes()) != expected:
                raise ValueError('Worktree checkout changed frozen bytes: ' + path)
    coordinator=TDDCoordinator(contract,integration.path,rules,test_config_paths=tuple(frozen))
    red=json.loads((ROOT/'red-corrected.json').read_bytes())
    result=TestResult(**{key:tuple(value) if isinstance(value,list) else value for key,value in red['tests'].items()})
    evidence=BehaviorEvidence(red['request']['candidate_revision'],TESTS,result)
    coordinator.approve_tests('T','Explicit deterministic fixture review: positive/negative credit, score/cap and shared composition; five live assertion failures. Not model-judge acceptance.')
    for id in units:
        coordinator.record_baseline(id,evidence)
    coordinator.freeze()
    hosts={id:ExecutionHost(handle,contract,rules,frozen_paths=tuple(frozen)) for id,handle in units.items()}
    rejected=[]
    for path in (TEST,CODE[1]):
        try:
            hosts['A'].write_file(path,b'forbidden')
        except ValueError:
            rejected.append(path)
        else:
            raise AssertionError('Ownership protection failed')
    emit('ownership-rejections',rejected)
    barrier=Barrier(2)
    timings={}
    def code(unit):
        timings[unit.id]={'start':time.monotonic()}
        barrier.wait(timeout=10)
        name='CreditCalculator' if unit.id=='A' else 'ScoreCalculator'
        expression='current + System.Math.Max(0, amount)' if unit.id=='A' else 'System.Math.Min(100, current + amount)'
        content=f'namespace FrameworkDemo {{ public sealed class {name} {{ public int Calculate(int current, int amount) => {expression}; }} }}\n'.encode()
        hosts[unit.id].write_file(unit.owns[0],content)
        timings[unit.id]['finish']=time.monotonic()
        return {unit.owns[0]:content}
    candidates=dispatch_parallel(coordinator,code)
    if any(c.violation for c in candidates):
        raise ValueError(str(candidates))
    assert max(t['start'] for t in timings.values()) < min(t['finish'] for t in timings.values())
    emit('parallel-coding',{'kind':'deterministic fixture callbacks, not real model calls','timings':timings})
    for id in units:
        coordinator.pending_shared(id)
    first=manager.integrate(integration,manager.capture(units['A']),{})
    req,partial=verify('partial-shared',integration.path,(TESTS[4],))
    assert partial.failed==(TESTS[4],)
    shared=shared_failure(contract,VerificationResult(req,'tests','failed',failed_tests=partial.failed,
                          test_result=partial,behavioral=True),{'A':first,'B':baseline['commit']})
    emit('shared-attribution',{'evidence_id':shared.evidence_id,'implementing_units':shared.implementing_units,
                              'test_authors':shared.test_authors,'action':'wait for declared B candidate; do not blame or retry A'})
    final=manager.integrate(integration,manager.capture(units['B']),{})
    req,green=verify('green',integration.path)
    if set(green.passed)!=set(TESTS) or green.failed or green.skipped or green.inconclusive:
        raise ValueError('Isolated full suite did not turn Green')
    coordinator.record_group_green(('A','B'),BehaviorEvidence(req.candidate_revision,TESTS,green))
    for id in units:
        coordinator.finish_refactor(id,reason='Single pure expression; no duplication or unnecessary state. No-change refactor decision after live Green.')
    req,confirmed=verify('refactor-confirmed',integration.path)
    assert set(confirmed.passed)==set(TESTS) and not confirmed.failed
    for path,expected in frozen.items():
        assert digest((integration.path/path).read_bytes())==expected
        assert digest((GAME/path).read_bytes())==expected
        for handle in units.values():
            assert digest((handle.path/path).read_bytes())==expected
    coordinator.assert_frozen()
    emit('summary',{'scope':'isolated Editor-only diagnostic; existing game failures excluded by explicit user decision',
                   'baseline_commit':baseline['commit'],'integration_commit':final,'snapshot':req.candidate_revision,
                   'units':{id:asdict(coordinator.state(id)) for id in units},'frozen_inputs_preserved':True,
                   'red_failed':5,'green_passed':5,'refactor_passed':5,'shared_failure_units':list(shared.implementing_units),
                   'real_models':False,'human_accepted':False})
    print('Isolated multi-unit demonstration complete',flush=True)

if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare()
    elif sys.argv[1:] == ['red']:
        freeze_red()
    elif sys.argv[1:] == ['demonstrate']:
        demonstrate()
    else:
        raise SystemExit('Use prepare, red (preparation recovery), or demonstrate')
