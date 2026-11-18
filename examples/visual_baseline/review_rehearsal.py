"""Trusted operator rehearsal, not a coder tool or production human authenticator.

Only explicit chat decisions are imported as receipts by the operator. Fault
injection is a diagnostic outside a frozen coding cycle; it never grants a coder
permission to write presentation assets. No model calls or budget resets occur.
"""
from dataclasses import asdict, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import sys
import time

import live
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.evidence import TestResult
from unity_coder.core.lifecycle import RunLifecycle
from unity_coder.core.review import ReviewGate
from unity_coder.core.verification import VerificationRequest, VerificationResult

ROOT = Path(os.environ['VISUAL_REVIEW_ROOT']).resolve()
RUN = 'visual-review-live1'
EVIDENCE = ROOT/'evidence'
REPO_EVIDENCE = live.SOURCE/'openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/live-evidence/visual-review'
SHELL = 'Runtime/Script/FrameworkVisualDemo/ExpeditionPreviewShell.cs'
TEST = 'Tests/Runtime/Script/FrameworkVisualDemo/VisualInteractionTests.cs'
TESTS = live.TESTS + tuple('FrameworkVisualDemo.Tests.Interactions.'+name for name in (
    'ConfirmUsesThePreparedBindingToShowReady','ResetRestoresThePreparedPreviewState'))
CORAL_TEST='FrameworkVisualDemo.Tests.CoralPresentation.PrimaryButtonUsesTheRequestedWarmCoral'


def save(name: str, value: object) -> None:
    for folder in (EVIDENCE,REPO_EVIDENCE):
        folder.mkdir(parents=True,exist_ok=True)
        (folder/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')


def baseline_files() -> dict[str, bytes]:
    manifest = json.loads((live.SOURCE/'openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/live-evidence/visual-baseline/presentation.v1.json').read_text())
    return {item['path']:(live.GAME/item['path']).read_bytes() for item in manifest['files']}


def identity(files: dict[str, bytes]) -> str:
    return sha256(json.dumps({p:sha256(b).hexdigest() for p,b in files.items()},sort_keys=True).encode()).hexdigest()


def candidate_files() -> dict[str, bytes]:
    files=baseline_files()
    test_root=live.GAME/'Tests/Runtime/Script/FrameworkVisualDemo'
    for path in test_root.glob('*'):
        if path.is_file():files[path.relative_to(live.GAME).as_posix()]=path.read_bytes()
    return files


def request(version: int, label: str, selection: tuple[str,...]) -> VerificationRequest:
    files = candidate_files()
    snapshot=identity(files)
    return VerificationRequest(label+'-'+snapshot[:12],RUN,version,'visual-review-contract-v'+str(version),
        snapshot,'visual-presentation-v'+str(version),'isolated-demo-profile','dedicated-host',selection,True)


def gate(version: int, token: str) -> ReviewGate:
    result=ReviewGate(RunLifecycle(ROOT,RUN,contract_version=version,contract_sha256='visual-review-contract-v'+str(version)),
        authenticate_human=lambda value:'chat-user' if secrets.compare_digest(value,token) else None)
    # Component rehearsal retains each version's review; this is not an executor migration.
    if version>1:
        result.path=result.lifecycle.prefix+'/review-v'+str(version)+'.json'
        result.guard=result.lifecycle.prefix+'/review-v'+str(version)+'.guard'
    return result


def verify(version: int, label: str, selection: tuple[str,...]) -> VerificationResult:
    req=request(version,label,selection)
    worker=live.BridgeTransport(live.HOST,ports=(live.PORT,),timeout=180)
    compile_result=worker.compile(req)
    if not compile_result.compilation or not compile_result.compilation.passed or compile_result.compilation.operational_error:
        raise ValueError('Candidate did not compile')
    # Compilation can return just before the domain reload reconnects. Wait using
    # read-only capabilities; do not issue another refresh or replay a mutation.
    stable=0
    for _ in range(60):
        try:
            reply=live.command('FrameworkVerifyCapabilities')
            capability=json.loads(str(reply.get('data','{}')))
            stable=stable+1 if capability.get('ready') and not capability.get('active_ticket') else 0
            if stable>=2:break
        except (OSError,ValueError):stable=0
        time.sleep(1)
    else:raise TimeoutError('Editor did not settle after compilation')
    result=worker.run_tests(req)
    tests=result.tests
    if tests is None or tests.operational_error or tests.skipped or tests.inconclusive or set(tests.executed)!=set(selection):
        save(label+'-operational',asdict(result))
        raise ValueError('Incomplete live test evidence: '+str(tests.operational_error if tests else 'no test result'))
    status='failed' if tests.failed else 'passed'
    evidence=VerificationResult(req,'tests',status,test_result=tests,failed_tests=tests.failed,
        full_suite_verified=not tests.failed,behavioral=True)
    raw=asdict(evidence)
    raw['test_result']['discovered']=list(selection)
    save(label,raw)
    save(label+'-compile',asdict(compile_result))
    if request(version,label,selection)!=req:
        raise ValueError('Candidate changed during verification')
    print(label,status,len(tests.passed),len(tests.failed),flush=True)
    return evidence


def load_evidence(label: str) -> VerificationResult:
    data=json.loads((EVIDENCE/(label+'.json')).read_text())
    raw=data['request'];raw['test_selection']=tuple(raw['test_selection'])
    result=data['test_result']
    tests=TestResult(**{k:tuple(v) if isinstance(v,list) else v for k,v in result.items()})
    return VerificationResult(VerificationRequest(**raw),'tests',data['status'],test_result=tests,
        failed_tests=tuple(data['failed_tests']),full_suite_verified=data['full_suite_verified'],behavioral=True)


def main() -> None:
    action=sys.argv[1]
    budget=BudgetLedger(ROOT,RUN,input_limit=100000,output_limit=32768,max_cycles=3,max_added_units=2)
    budget.begin_cycle(1,'visual-review-contract-v1',{'preview':('preview',)})
    token=secrets.token_urlsafe(32)
    review=gate(1,token)
    if action=='accept-baseline':
        receipt=json.loads((ROOT/'human-baseline-approval.json').read_text())
        approved=json.loads((live.SOURCE/'openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/live-evidence/visual-baseline/review.json').read_text())
        if receipt['manifest_identity']!=approved['manifest_identity'] or receipt['decision']!='accept':
            raise ValueError('Receipt does not approve this baseline')
        manifest=json.loads((live.SOURCE/'openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/live-evidence/visual-baseline/presentation.v1.json').read_text())
        files=baseline_files()
        if any(sha256(files[r['path']]).hexdigest()!=r['sha256'] for r in manifest['files']):
            raise ValueError('Approved baseline bytes changed')
        evidence=verify(1,'approved-baseline',live.TESTS)
        review.offer(evidence,files,evidence_refs=('evidence/approved-baseline.json',))
        save('baseline-acceptance',review.decide(token,evidence.request,'accept',findings=()))
        save('human-baseline-approval',receipt)
    elif action in ('inject','verify-fault'):
        original=(live.SOURCE/'examples/visual_baseline/ExpeditionPreviewShell.cs').read_bytes()
        if action=='inject' and (live.GAME/SHELL).read_bytes()!=original:
            raise ValueError('Unexpected shell bytes before controlled fault')
        if action=='inject': live.copy_new(live.SOURCE/'examples/visual_baseline/VisualInteractionTests.cs',TEST)
        # Deliberate diagnostic mutation, kept in evidence and restored by repair.
        broken=original.replace(b'statusText.text = "READY FOR REVIEW";',b'statusText.text = "BASELINE PREVIEW";')
        if action=='inject': (live.GAME/SHELL).write_bytes(broken)
        elif (live.GAME/SHELL).read_bytes()!=broken: raise ValueError('Unexpected fault bytes')
        live.refresh()
        evidence=verify(1,'broken-interaction',TESTS)
        if len(evidence.failed_tests)!=1 or not evidence.failed_tests[0].endswith('ConfirmUsesThePreparedBindingToShowReady'):
            raise ValueError('Expected only the injected primary-button failure')
        old=load_evidence('approved-baseline')
        try:
            review.finalize(old.request,parent_revision=old.request.candidate_revision,completion_revision='diagnostic-only',files=baseline_files())
        except ValueError as error:
            save('changed-source-approval-rejected',{'rejected':True,'reason':str(error),'fault':'primary button does not show ready'})
        else: raise AssertionError('Changed source reused old approval')
        try:
            review.offer(evidence,baseline_files(),evidence_refs=('evidence/broken-interaction.json',))
        except ValueError as error:
            save('broken-candidate-not-offered',{'rejected':True,'reason':str(error)})
        else: raise AssertionError('Failing candidate offered for acceptance')
    elif action in ('repair','repair-resume'):
        original=(live.SOURCE/'examples/visual_baseline/ExpeditionPreviewShell.cs').read_bytes()
        expected=original.replace(b'statusText.text = "READY FOR REVIEW";',b'statusText.text = "BASELINE PREVIEW";')
        expected = original if action=='repair-resume' else expected
        if (live.GAME/SHELL).read_bytes()!=expected: raise ValueError('Controlled fault changed unexpectedly')
        (live.GAME/SHELL).write_bytes(original)
        live.refresh()
        evidence=verify(1,'repaired-interaction',TESTS)
        if evidence.status!='passed': raise ValueError('Repair failed')
        review.offer(evidence,baseline_files(),evidence_refs=('evidence/repaired-interaction.json',))
        old=load_evidence('approved-baseline')
        try: review.decide(token,old.request,'accept',findings=())
        except ValueError as error: save('old-request-rejected',{'rejected':True,'reason':str(error)})
        else: raise AssertionError('Old review request accepted')
        save('repair-continuity',{'contract_version':1,'budget_totals':budget.totals(),'model_calls':0,
            'source_restored_exactly':(live.GAME/SHELL).read_bytes()==original,'human_acceptance':'pending'})
    elif action=='request-rework':
        receipt=json.loads((ROOT/'human-presentation-request.json').read_text())
        if receipt['decision']!='contract' or receipt['finding']!='Change the primary button to warm coral':
            raise ValueError('Unexpected human presentation request')
        evidence=load_evidence('repaired-interaction')
        save('presentation-rework',review.decide(token,evidence.request,'contract',findings=(receipt['finding'],)))
        save('human-presentation-request',receipt)
        result=review.lifecycle.finish('rework',candidate_revision=evidence.request.candidate_revision,
            reason=receipt['finding'],evidence_refs=('evidence/presentation-rework.json',))
        save('rework-result',result)
    elif action=='coral-red':
        if review.state()['decision']!='contract': raise ValueError('Human presentation rework required')
        budget.begin_cycle(2,'visual-review-contract-v2',{'preview':('preview',)})
        live.copy_new(live.SOURCE/'examples/visual_baseline/CoralPresentationTests.cs',
            'Tests/Runtime/Script/FrameworkVisualDemo/CoralPresentationTests.cs')
        live.refresh()
        evidence=verify(2,'coral-red',TESTS+(CORAL_TEST,))
        if evidence.failed_tests!=(CORAL_TEST,): raise ValueError('Expected only the requested coral requirement to fail')
    elif action=='coral-review':
        budget.begin_cycle(2,'visual-review-contract-v2',{'preview':('preview',)})
        evidence=verify(2,'coral-ready',TESTS+(CORAL_TEST,))
        if evidence.status!='passed': raise ValueError('Coral candidate did not pass')
        current=gate(2,token)
        current.offer(evidence,candidate_files(),evidence_refs=('evidence/coral-ready.json',))
        old=load_evidence('approved-baseline')
        try: current.decide(token,old.request,'accept',findings=())
        except ValueError as error: save('v1-approval-rejected-for-v2',{'rejected':True,'reason':str(error)})
        else: raise AssertionError('Old version approval accepted')
        save('coral-review',current.state())
        save('continuity',{'run_id':RUN,'contract_versions':[1,2],'budget_totals':budget.totals(),
            'model_calls':0,'budget_reset':False,'review_boundary':'live component rehearsal, not a new exported-graph run'})
    elif action=='prepare-v2-report':
        brief=live.GAME/'Editor/ArtSource~/FrameworkVisualDemo/design.md'
        original=(live.SOURCE/'examples/visual_baseline/design.md').read_bytes()
        revised=original+b'\n## Revision 2: human presentation request\n\nThe primary button is now warm coral (#F6A98B). Its label, geometry, bindings,\nsecondary button, illustration and runtime status colors remain as in version 1.\n'
        if brief.read_bytes() not in (original,revised): raise ValueError('Unexpected synthetic brief changes')
        brief.write_bytes(revised)
        response=live.command('FrameworkPrepareVisual',operation='inspect')
        if response.get('status')!='success':raise ValueError(str(response))
        report=json.loads(response['data']);report['revision']='visual-baseline-v2'
        (live.OUTPUT/'editor-report.v2.json').write_text(json.dumps(report,indent=2))
    elif action=='accept-v2':
        receipt=json.loads((ROOT/'human-v2-approval.json').read_text())
        evidence=load_evidence('coral-ready')
        if receipt['decision']!='accept' or receipt['candidate_revision']!=evidence.request.candidate_revision:
            raise ValueError('Human receipt does not approve the offered v2 candidate')
        if identity(candidate_files())!=evidence.request.candidate_revision:
            raise ValueError('Candidate changed since verification')
        current=gate(2,token)
        save('v2-acceptance',current.decide(token,evidence.request,'accept',findings=()))
        save('human-v2-approval',receipt)
    else: raise ValueError('Unknown rehearsal action')
    save('budget',json.loads((ROOT/budget.path).read_text()))


if __name__=='__main__':main()
