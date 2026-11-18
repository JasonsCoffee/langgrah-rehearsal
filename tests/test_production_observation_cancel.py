"""In-flight production progress and cancellation; no network or editor."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time

from test_contracts import bundle
from test_workspaces import workspace, git
from test_local_executor import local, run


def test_progress_and_heartbeat_continue_during_blocking_verification(local):
    executor,services,_,_,_,_=local
    entered,release=Event(),Event()
    original=services.verifier
    def blocked(request,root,patches):
        entered.set()
        assert release.wait(5)
        return original(request,root,patches)
    executor.advance('prepare')
    services.verifier=blocked
    with ThreadPoolExecutor(1) as pool:
        future=pool.submit(executor.advance,'red')
        try:
            assert entered.wait(3)
            deadline=time.monotonic()+3
            seen=[]
            while time.monotonic()<deadline:
                status=executor.progress.status()
                if status.get('active_verification'):
                    seen.append(status)
                    if len(seen)>1 and seen[-1]['sequence']>seen[0]['sequence']:break
                time.sleep(.05)
            assert len(seen)>1
            assert seen[-1]['stage']=='red'
            assert seen[-1]['active_verification']==git(services.integration.path,'rev-parse','HEAD')
            assert set(seen[-1]['attempts'])==set(services.tdd.units)
        finally:release.set()
        future.result()
    sequence=executor.progress.status()['sequence']
    time.sleep(.7)
    assert executor.progress.status()['sequence']==sequence


def test_cancel_during_coding_joins_workers_and_prevents_integration(local):
    executor,services,workers,_,repo,_=local
    entered,release=Event(),Event()
    original=workers.code
    def blocked(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    workers.code=blocked
    with ThreadPoolExecutor(1) as pool:
        future=pool.submit(run,executor)
        try:
            assert entered.wait(3)
            executor.request_cancel()
        finally:release.set()
        assert future.result()['outcome']=='cancelled'
    assert git(services.integration.path,'rev-parse','HEAD')==git(repo,'rev-parse','HEAD')
    assert all(stage=='green' for _,stage in workers.calls)
    assert executor.outcome()=='cancelled'


def test_cancel_during_verification_preserves_evidence_without_new_coding(local):
    executor,services,workers,_,_,_=local
    entered,release=Event(),Event()
    original=services.verifier
    def blocked(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    services.verifier=blocked
    with ThreadPoolExecutor(1) as pool:
        future=pool.submit(run,executor)
        try:
            assert entered.wait(3)
            executor.request_cancel()
        finally:release.set()
        assert future.result()['outcome']=='cancelled'
    assert workers.calls==[]
    assert list((executor.root/services.prefix/'evidence').glob('*.json'))
