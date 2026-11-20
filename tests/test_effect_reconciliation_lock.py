"""Frozen concurrency boundary: reconciliation cannot race a live effect."""
from hashlib import sha256
from threading import Event
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_contracts import bundle
from test_workspaces import workspace
from test_local_executor import local


def test_live_effect_finishes_before_reconciliation_can_inspect(local):
    executor,services,_,_,_,_ = local
    effects=services.effects; identity={'unit':'U0-tests'}
    entered=Event(); release=Event(); attempted=Event(); called=[]
    def invoke():
        entered.set()
        assert release.wait(5)
        return {'actual':'result'}
    def resolve():
        attempted.set()
        effects.reconcile_call('live',identity,reconcile=lambda record:called.append(record))
    with ThreadPoolExecutor(max_workers=2) as pool:
        live=pool.submit(effects.call,'live',identity,invoke)
        assert entered.wait(5)
        reconciliation=pool.submit(resolve)
        assert attempted.wait(5)
        try:
            # A validator must not run on the intent of a still-active request.
            assert not reconciliation.done()
        finally:
            release.set()
        assert live.result() == {'actual':'result'}
        with pytest.raises(ValueError):reconciliation.result()
    assert called == []
    assert effects.read('live')['result'] == {'actual':'result'}
