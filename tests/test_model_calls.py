"""Paid calls reserve first and reconcile durable replies without replay."""
import pytest
from test_ai_models import config, response
from unity_coder.core.ai_models import load_ai_config, ModelClient, ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.model_calls import ModelCalls, JudgeInput, judge_prompt


def setup(tmp_path, send):
    settings=load_ai_config(config(tmp_path))
    budget=BudgetLedger(tmp_path/'state','run',input_limit=10000,output_limit=1000,max_cycles=3,max_added_units=2)
    budget.begin_cycle(1,'contract',{'A':('A',)})
    return ModelCalls(ModelClient(settings.coder,transport=send),budget,'run'),budget


def test_reply_replay_does_not_repeat_paid_call(tmp_path):
    seen=[]
    calls,budget=setup(tmp_path,lambda *args: seen.append(args) or response())
    first=calls.generate('call1','A','Code',max_output_tokens=64)
    assert calls.generate('call1','A','Code',max_output_tokens=64)==first
    assert len(seen)==1 and budget.totals()==(8,2)
    with pytest.raises(ValueError): calls.generate('call1','A','Different',max_output_tokens=64)


def test_uncertain_call_keeps_reservation_and_is_not_repeated(tmp_path):
    seen=[]
    def fail(*args): seen.append(1); raise OSError('timeout')
    calls,budget=setup(tmp_path,fail)
    with pytest.raises(ModelError): calls.generate('call1','A','Code',max_output_tokens=64)
    reserved=budget.totals()
    assert reserved[0]>0 and reserved[1]==64
    with pytest.raises(ModelError): calls.generate('call1','A','Code',max_output_tokens=64)
    assert len(seen)==1 and budget.totals()==reserved


def test_exhaustion_prevents_provider_dispatch(tmp_path):
    seen=[]
    calls,budget=setup(tmp_path,lambda *args:seen.append(1) or response())
    budget.reserve('other','A',10000,1000)
    with pytest.raises(ValueError): calls.generate('call1','A','Code',max_output_tokens=64)
    assert not seen


def test_durable_reply_recovers_usage_after_interrupted_reconcile(tmp_path,monkeypatch):
    seen=[]
    calls,budget=setup(tmp_path,lambda *args:seen.append(1) or response())
    original=budget.reconcile
    def fail(*args): raise OSError('crash before accounting')
    monkeypatch.setattr(budget,'reconcile',fail)
    with pytest.raises(OSError): calls.generate('call1','A','Code',max_output_tokens=64)
    monkeypatch.setattr(budget,'reconcile',original)
    assert calls.generate('call1','A','Code',max_output_tokens=64).text=='OK'
    assert len(seen)==1 and budget.totals()==(8,2)


def test_judge_context_has_only_evidence_fields():
    evidence=JudgeInput('criterion','spec',{'gate':'tests','failed':['T']},{'source.txt':'A'},{'source.txt':'full contents'})
    prompt=judge_prompt(evidence)
    assert all(value in prompt for value in ('criterion','spec','full contents','source.txt'))
    with pytest.raises(TypeError):
        JudgeInput('criterion','spec',{}, {}, {}, notes='trust coder', author='coder-model')
