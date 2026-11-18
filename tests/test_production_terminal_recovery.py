"""Known review decisions and metadata completion survive stage interruption."""
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from test_local_executor import local, run
from test_production_effect_recovery import Crash, reopen
from unity_coder.core.local_executor import TestReviewRejected, _verification
from unity_coder.core.completion import CandidateCompletion


def test_rejected_review_is_not_repeated_after_receipt_crash(local, monkeypatch):
    import unity_coder.core.local_executor as module
    executor,services,workers,_,_,_=local
    calls=[]
    def reject(*args):
        calls.append(args[-1])
        raise TestReviewRejected('Missing behavior')
    workers.review_tests=reject
    original=module.atomic_write
    def crash(root,path,content):
        if '/receipts/' in path:raise Crash()
        return original(root,path,content)
    monkeypatch.setattr(module,'atomic_write',crash)
    with pytest.raises(Crash):executor.advance('prepare')
    monkeypatch.setattr(module,'atomic_write',original)
    reopened=reopen(executor,services)
    executor.advance('prepare')
    assert executor.stage()=='prepare'
    assert reopened.tdd.state('U0-tests').preparation_attempts==1
    assert len(calls)==1


def test_completion_commit_recovers_through_production_executor(local,monkeypatch):
    executor,services,workers,_,_,review=local
    run(executor)
    evidence=_verification(services.state['verification'])
    review.decide('credential',evidence.request,'accept',findings=())
    executor.resume_review()
    publish=CandidateCompletion._publish
    def crash(self,before,after):
        publish(self,before,after)
        raise Crash()
    monkeypatch.setattr(CandidateCompletion,'_publish',crash)
    with pytest.raises(Crash):executor.advance('finalize')
    head=git(services.integration.path,'rev-parse','HEAD')
    calls=list(workers.calls)
    monkeypatch.setattr(CandidateCompletion,'_publish',publish)
    reopened=reopen(executor,services)
    assert run(executor)['outcome']=='pass'
    assert git(reopened.integration.path,'rev-parse','HEAD')==head
    assert workers.calls==calls
