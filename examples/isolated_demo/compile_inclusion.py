"""Prove that a newly added source is included by the live compile backend."""
from dataclasses import asdict
import time
import run as demo


def main() -> None:
    relative=demo.PREFIX+'/Code/NewFileInclusionProbe.cs'
    path=demo.GAME/relative
    metadata=path.with_suffix(path.suffix+'.meta')
    if path.exists() or metadata.exists():
        raise ValueError('Compile probe destination already exists')
    before=demo.snapshot(demo.GAME)
    source=b'#error FRAMEWORK_NEW_FILE_PROBE\n'
    contract=demo.load_contract((demo.REPO/'specs/demo/contract.v1.json').read_bytes(),demo.REPO,demo.UnityAdapter())
    def request(label):
        return demo.VerificationRequest('new-file-'+demo.ATTEMPT+'-'+label,'compile-inclusion',1,contract.sha256,
            demo.snapshot(demo.GAME),contract.presentation_ref.sha256,contract.coding_profile_ref.sha256,
            contract.environment_ref.sha256,demo.TESTS,True)
    worker=demo.BridgeTransport(demo.HOST,ports=(demo.PORT,),timeout=180)
    negative=None
    started=time.monotonic()
    try:
        path.write_bytes(source)
        demo.refresh()
        negative=worker.compile(request('invalid'))
        demo.emit('compile-inclusion-negative',asdict(negative))
        if (negative.compilation.operational_error or negative.compilation.passed
            or not any('FRAMEWORK_NEW_FILE_PROBE' in v.message for v in negative.compilation.violations)):
            raise ValueError('New invalid source did not produce its expected compile diagnostic')
        print('New-file inclusion proved by compiler diagnostic',flush=True)
    finally:
        if path.exists():
            if path.read_bytes()!=source:
                raise ValueError('Probe changed unexpectedly; preserve for reconciliation')
            path.unlink()
        metadata.unlink(missing_ok=True)
        demo.refresh()
        positive=worker.compile(request('restored'))
        demo.emit('compile-inclusion-restored',asdict(positive))
        if positive.compilation.operational_error or not positive.compilation.passed:
            raise ValueError('Host failed to recover after removing the owned probe')
        if demo.snapshot(demo.GAME)!=before:
            raise ValueError('Host fixture differs from its pre-probe snapshot')
    demo.emit('compile-inclusion-summary',{'new_file_failure_observed':True,'restored_compile_passed':True,
        'snapshot_preserved':True,'elapsed_seconds':time.monotonic()-started,'source':relative})
    print('Compile inclusion probe complete; original fixture restored',flush=True)


if __name__=='__main__': main()
