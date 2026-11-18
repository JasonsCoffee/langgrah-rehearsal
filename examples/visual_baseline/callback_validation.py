"""Explicit isolated diagnostic selection; never runs the existing game suite."""
from dataclasses import asdict
from hashlib import sha256
import json
import time
import live
from unity_coder.core.tdd import BehaviorEvidence, validate_behavior
from unity_coder.core.verification import VerificationRequest

EVIDENCE=live.SOURCE/'openspec/changes/formalize-unity-feature-delivery/live-evidence/callback-validation'
PROBE='Tests/Runtime/Script/FrameworkCallbackProbe/CallbackProbeTests.cs'
HELPER='Editor/Script/FrameworkVerification/UnityCoderVerifier.cs'


def save(label: str, value: object) -> None:
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/(label+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')


def main() -> None:
    # Snapshot the accepted demonstration, independently from temporary probes.
    manifest=json.loads((live.SOURCE/'openspec/changes/formalize-unity-feature-delivery/live-evidence/visual-baseline/presentation.v1.json').read_bytes())
    before={row['path']:sha256((live.GAME/row['path']).read_bytes()).hexdigest() for row in manifest['files']}
    helper=live.SOURCE/'unity/Editor/UnityCoderVerifier.cs'
    (live.GAME/HELPER).write_bytes(helper.read_bytes())
    live.copy_new(live.SOURCE/'examples/visual_baseline/CallbackProbeTests.cs',PROBE)
    live.refresh()
    worker=live.BridgeTransport(live.HOST,ports=(live.PORT,),timeout=180)
    stamp=str(time.time_ns())
    def request(label: str, selection: tuple[str,...]) -> VerificationRequest:
        return VerificationRequest('callback-'+stamp+'-'+label,'callback-validation',1,
            'isolated-callback-diagnostics',sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
            'accepted-lake-presentation','isolated-demo-profile','dedicated-host',selection,False)
    demo=live.TESTS+tuple('FrameworkVisualDemo.Tests.Interactions.'+name for name in (
        'ConfirmUsesThePreparedBindingToShowReady','ResetRestoresThePreparedPreviewState'))+(
        'FrameworkVisualDemo.Tests.CoralPresentation.PrimaryButtonUsesTheRequestedWarmCoral',)
    compiled=worker.compile(request('compile',demo))
    save('compile',asdict(compiled))
    assert compiled.compilation.passed and not compiled.compilation.operational_error
    for _ in range(60):
        time.sleep(1)
        try:
            status=json.loads(str(live.command('FrameworkVerifyCapabilities')['data']))
            if status.get('ready') and not status.get('active_ticket'):
                time.sleep(2)
                break
        except (OSError,ValueError):pass
    cases=(('demo',demo,'assertion'),
           ('assertion',('FrameworkCallbackProbe.Assertion.FailsWithAssertion',),'assertion'),
           ('setup',('FrameworkCallbackProbe.Setup.CannotRun',),'setup'),
           ('suite-teardown',('FrameworkCallbackProbe.SuiteTeardown.PassesBeforeTeardown',),'setup'))
    for label,selection,kind in cases:
        req=request(label,selection)
        evidence=worker.run_tests(req)
        save(label,asdict(evidence))
        result=evidence.tests
        assert result and not result.operational_error and set(result.executed)==set(selection)
        assert result.failure_kind==kind,(label,result)
        if label=='demo':assert set(result.passed)==set(selection) and not result.failed
        elif label=='suite-teardown':assert result.passed==selection and not result.failed and result.messages
        else:assert result.failed==selection and result.messages
        if kind=='setup':
            try:validate_behavior(BehaviorEvidence(req.candidate_revision,selection,result),selection)
            except ValueError:pass
            else:raise AssertionError('Setup failure admitted as behavioral evidence')
        print(label,kind,len(result.passed),len(result.failed),flush=True)
    after={p:sha256((live.GAME/p).read_bytes()).hexdigest() for p in before}
    assert before==after
    originals=json.loads((live.OUTPUT/'original-files.json').read_bytes())
    changed=[p for p,d in originals.items() if not (live.GAME/p).is_file() or sha256((live.GAME/p).read_bytes()).hexdigest()!=d]
    assert not changed,changed
    save('integrity',{'original_files':len(originals),'changed':changed,'presentation_unchanged':before==after,
        'helper_sha256':sha256(helper.read_bytes()).hexdigest(),'presentation_files':after})
    # Remove only the diagnostics created above, retaining every receipt.
    target=live.GAME/PROBE
    assert target.read_bytes()==(live.SOURCE/'examples/visual_baseline/CallbackProbeTests.cs').read_bytes()
    target.unlink()
    meta=target.with_suffix('.cs.meta')
    if meta.exists():meta.unlink()
    live.refresh()


if __name__=='__main__':main()
