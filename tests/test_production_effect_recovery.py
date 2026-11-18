"""Crash recovery exercises actual production stages and disposable Git commits."""
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from test_local_executor import local, run
from unity_coder.core.local_executor import LocalExecutionServices


class Crash(BaseException):pass


def reopen(executor, services):
    executor.services=LocalExecutionServices(services.manager,services.integration,services.budget,
        services.workers,services.verifier,services.review,preflight=services.preflight)
    return executor.services


def test_crash_after_commit_recognizes_apply_and_does_not_recode(local):
    executor,services,workers,_,_,_=local
    executor.advance('prepare');executor.advance('red')
    original=services.manager.integrate
    heads=[]
    def crash(*args):
        head=original(*args)
        heads.append(head)
        raise Crash()
    services.manager.integrate=crash
    with pytest.raises(Crash):executor.advance('code')
    services.manager.integrate=original
    reopened=reopen(executor,services)
    assert run(executor)['outcome']=='awaiting_human_review'
    assert len([c for c in workers.calls if c[1]=='green'])==2
    assert git(reopened.integration.path,'merge-base','--is-ancestor',heads[0],'HEAD')==''


def test_crash_before_service_receipt_reuses_verification(local,monkeypatch):
    import unity_coder.core.local_executor as module
    executor,services,workers,verified,_,_=local
    executor.advance('prepare');executor.advance('red');executor.advance('code')
    write=module.atomic_write
    def crash(root,path,content):
        if '/receipts/' in path and path.endswith('-verify.json'):raise Crash()
        return write(root,path,content)
    monkeypatch.setattr(module,'atomic_write',crash)
    with pytest.raises(Crash):executor.advance('verify')
    count=len(verified)
    monkeypatch.setattr(module,'atomic_write',write)
    reopen(executor,services)
    executor.advance('verify')
    assert len(verified)==count
    assert executor.stage()=='refactor'
