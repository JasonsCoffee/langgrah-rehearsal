"""Recovery preserves rollback bases and cancellation despite worker errors."""
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from test_local_executor import local, run
from test_production_effect_recovery import Crash, reopen
from unity_coder.core.local_executor import WorkerPatch
from unity_coder.core.ai_models import ModelError


def test_restore_commit_replays_with_original_intent_base(local,monkeypatch):
    executor,services,workers,_,_,_=local
    original=workers.code
    def code(unit,stage,files,feedback,operation):
        if stage=='refactor':return WorkerPatch({p:b'broken' for p in unit.owns},'Diagnostic regression')
        return original(unit,stage,files,feedback,operation)
    workers.code=code
    for stage in ('prepare','red','code','verify','refactor'):executor.advance(stage)
    apply=services.manager.integrate
    def crash(*args):
        apply(*args)
        raise Crash()
    monkeypatch.setattr(services.manager,'integrate',crash)
    with pytest.raises(Crash):executor.advance('final_verify')
    monkeypatch.setattr(services.manager,'integrate',apply)
    reopened=reopen(executor,services)
    executor.advance('final_verify')
    assert executor.stage()=='code'
    assert all((reopened.integration.path/p).read_bytes()==b'implemented'
               for u in reopened.contract.units if u.role=='impl' for p in u.owns)
    assert reopened.retry.state('U1-state').regressions==1


def test_cancellation_remains_authoritative_after_model_error(local):
    executor,services,workers,verified,_,_=local
    executor.advance('prepare');executor.advance('red')
    def code(*args):
        executor.request_cancel()
        raise ModelError('Provider ended without usable response')
    workers.code=code
    executor.advance('code')
    assert executor.outcome()=='cancelled'
    assert len(verified)==1


def test_uncertain_paid_call_is_retained_and_never_automatically_repeated(local):
    executor,services,workers,_,_,_=local
    calls=[]
    def crash(*args):
        calls.append(args[-1])
        raise Crash()
    workers.review_tests=crash
    with pytest.raises(Crash):executor.advance('prepare')
    reopen(executor,services)
    executor.advance('prepare')
    assert executor.outcome()=='operational'
    assert len(calls)==1
