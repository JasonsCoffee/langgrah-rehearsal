"""Qualification costs are bounded separately; ordinary coding stays globally charged."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


class Ledger:
    def __init__(self):self.data={'calls':{'historical':{'reserved':[100,20]}}}
    def _read(self):return self.data


def test_normal_review_is_not_pilot_usage_but_is_never_removed(tmp_path):
    from context_call_accounting import qualification_envelope
    ledger=Ledger();envelope=qualification_envelope(ledger,tmp_path)
    ledger.data['calls']['v70-step10-verify-judge-ECON']={'reserved':[20000000,32768]}
    ledger.data['calls']['v70-migration-pilot-coder-low']={'reserved':[1000,65536],'actual':[100,10]}
    before=repr(ledger.data)
    envelope.check(100000,32768)
    assert repr(ledger.data)==before
    assert qualification_envelope(ledger,tmp_path).before['limits']==[10000000,512000]


def test_unknown_selector_and_shadow_are_counted_in_full(tmp_path):
    from context_call_accounting import qualification_envelope
    from unity_coder.core.ai_models import ModelError
    ledger=Ledger();envelope=qualification_envelope(ledger,tmp_path)
    ledger.data['calls']['context-select-unknown']={'reserved':[8000000,8192]}
    ledger.data['calls']['v70-step10-verify-judge-ECON-shadow-audit']={'reserved':[1000000,32768]}
    with pytest.raises(ModelError):envelope.check(2000000,32768)
    assert 'actual' not in ledger.data['calls']['context-select-unknown']


def test_scope_record_is_bound_to_original_persistent_envelope(tmp_path):
    from context_call_accounting import qualification_envelope
    ledger=Ledger();qualification_envelope(ledger,tmp_path)
    path=tmp_path/'context-optimization/qualification-envelope-scope.json'
    assert path.exists()
    path.write_text('{}')
    with pytest.raises(ValueError):qualification_envelope(ledger,tmp_path)
