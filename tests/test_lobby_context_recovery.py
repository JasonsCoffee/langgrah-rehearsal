"""Frozen checks for the stale context fence and zero-submission recovery."""
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/codex_context_recovery.py')
    spec=importlib.util.spec_from_file_location('codex_context_recovery',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def test_codex_uses_final_prompt_staging_instead_of_legacy_byte_fence():
    module().enforce_context_limit(2091989,2000000,'codex','codex')
    from unity_coder.core.codex_stdio import context_parts
    assert len(context_parts('x'*2091989))==3
    with pytest.raises(Exception):context_parts('x'*2800000)


@pytest.mark.parametrize('providers',[('openrouter','openrouter'),('codex','openrouter')])
def test_other_routes_keep_the_original_fence(providers):
    with pytest.raises(ValueError):module().enforce_context_limit(2091989,2000000,*providers)


class Effects:
    def __init__(self,record):self.record=record;self.writes=[]
    def read(self,name):return self.record
    def write(self,name,value):self.writes.append((name,value));self.record=value


def test_only_real_judge_reply_completes_a_proven_unsubmitted_intent():
    identity={'request':{'candidate_revision':'exact'},'unit':'SHELL'}
    effects=Effects({'identity':identity});calls=[]
    def judge():calls.append('actual');return 'implementation','real independent reason'
    module().recover_judge_effect(effects,'judge-current',identity,False,judge)
    assert calls==['actual']
    assert effects.writes==[('judge-current',{'identity':identity,'result':{'classification':'implementation','reason':'real independent reason'}})]


@pytest.mark.parametrize('record,paid',[
    ({'identity':{'wrong':True}},False),
    ({'identity':{'unit':'SHELL'},'result':{'classification':'contract'}},False),
    ({'identity':{'unit':'SHELL'}},True),
])
def test_uncertain_completed_or_wrong_intents_never_call_judge(record,paid):
    effects=Effects(record);calls=[]
    with pytest.raises(ValueError):module().recover_judge_effect(effects,'judge-current',{'unit':'SHELL'},paid,lambda:calls.append('forbidden'))
    assert not calls and not effects.writes
