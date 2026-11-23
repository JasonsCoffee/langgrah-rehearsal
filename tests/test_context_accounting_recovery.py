"""Paid selector accounting and existing-run recovery are never reset."""
from pathlib import Path
import sys
import pytest
from unity_coder.core.ai_models import ModelError,ModelReply
from test_evidence_packet_manifest import packet

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_exact_selector_cache_does_not_spend_twice(tmp_path):
    from context_call_accounting import CachedSelectionCalls
    calls=[]
    class Fake:
        def generate(self,*args,**kwargs):calls.append(args);return ModelReply('{"selected":[]}',10,2,'id','deepseek-flash')
    c=CachedSelectionCalls(Fake(),tmp_path,'policy');p=packet()
    assert c.select(p,'U','prompt')==c.select(p,'U','prompt')
    assert len(calls)==1


def test_uncertain_selector_failure_is_not_replayed_or_refunded(tmp_path):
    from context_call_accounting import CachedSelectionCalls
    calls=[]
    class Fake:
        def generate(self,*args,**kwargs):calls.append(True);raise ModelError('unknown submission')
    c=CachedSelectionCalls(Fake(),tmp_path,'policy');p=packet()
    for _ in range(2):
        with pytest.raises(ModelError):c.select(p,'U','prompt')
    assert len(calls)==1


def test_migration_guard_detects_any_lost_charge_or_frozen_change():
    from mixed_backend_recovery import verify_preservation
    prior={'limits':[250000000,24000000,160,2],'calls':{'old':{'reserved':[5,7]}}}
    verify_preservation(prior,prior,{'Tests/T':'hash'},{'Tests/T':'hash'})
    with pytest.raises(ValueError):verify_preservation(prior,prior|{'calls':{}},{'T':'h'},{'T':'h'})
    with pytest.raises(ValueError):verify_preservation(prior,prior,{'T':'h'},{'T':'other'})
