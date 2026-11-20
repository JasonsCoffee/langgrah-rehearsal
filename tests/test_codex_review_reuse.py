"""Reuse needs the actual independent decision for byte-identical inputs."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import pytest
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.codex_backend import CodexModelClient,CodexPolicy
from unity_coder.core.model_calls import ModelCalls


def helper():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/codex_review_reuse.py')
    s=importlib.util.spec_from_file_location('codex_review_reuse_test',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def prepare(tmp_path):
    work=tmp_path/'worker';work.mkdir();state=tmp_path/'state'
    policy=CodexPolicy('judge','gpt-6.1-sol','medium','dispatch_accounting','approval.json',200)
    answer=json.dumps({'valid':True,'explanation':'Actual independent source review'})
    def exchange(_):
        yield {'method':'item/completed','params':{'threadId':'thread','turnId':'turn',
            'item':{'type':'agentMessage','phase':'final_answer','text':answer}}}
        yield {'method':'thread/tokenUsage/updated','params':{'threadId':'thread','turnId':'turn',
            'tokenUsage':{'total':{'inputTokens':8,'outputTokens':3,'cachedInputTokens':0,'reasoningOutputTokens':0,'totalTokens':11}}}}
        yield {'method':'turn/completed','params':{'threadId':'thread','turn':{'id':'turn','status':'completed'}}}
    client=CodexModelClient(policy,state,work,exchange=exchange,authorize=lambda _:True)
    budget=BudgetLedger(state,'run',input_limit=1000000,output_limit=100000,max_cycles=3,max_added_units=2)
    budget.begin_cycle(1,'contract',{'TEST-A':('TEST-A',)})
    calls=ModelCalls(client,budget,'run')
    prompt='Independently review test validity and coverage against the contract criteria.\n{"source":"exact"}'
    reply=calls.generate('old-review','TEST-A',prompt,max_output_tokens=32)
    return calls,prompt,reply


def test_exact_actual_review_reuses_original_reply_without_new_paid_call(tmp_path):
    calls,prompt,reply=prepare(tmp_path);before=calls.budget.totals()
    result=helper().reuse_review(calls,'new-review','TEST-A',prompt,32)
    assert result==reply and calls.budget.totals()==before
    assert not (calls.budget.root/calls.prefix/(sha256(b'new-review').hexdigest()+'.json')).exists()
    proofs=list((calls.budget.root/'review-reuse').glob('*.json'))
    assert len(proofs)==1 and json.loads(proofs[0].read_bytes())['actual_judge_call']=='old-review'


@pytest.mark.parametrize('bad',['prompt','unit','effort','output','negative','unknown-new'])
def test_any_changed_input_policy_or_pending_effect_requires_native_review(tmp_path,bad):
    calls,prompt,_=prepare(tmp_path);unit='TEST-A';limit=32
    if bad=='prompt':prompt+=' changed'
    elif bad=='unit':unit='TEST-B'
    elif bad=='effort':
        from dataclasses import replace
        calls.client.config=replace(calls.client.config,effort='low')
    elif bad=='output':limit=33
    elif bad=='negative':
        f=calls.budget.root/calls.prefix/(sha256(b'old-review').hexdigest()+'.json')
        d=json.loads(f.read_bytes());d['reply']['text']=json.dumps({'valid':False,'explanation':'rejected'});f.write_text(json.dumps(d))
    else:calls.budget.reserve('new-review','TEST-A',1,1)
    assert helper().reuse_review(calls,'new-review',unit,prompt,limit) is None


def test_unsettled_or_changed_actual_charge_cannot_supply_review(tmp_path):
    calls,prompt,_=prepare(tmp_path);ledger=calls.budget._read()
    ledger['calls']['old-review']['actual']=[0,0];calls.budget._save(ledger)
    with pytest.raises(ValueError):helper().reuse_review(calls,'new-review','TEST-A',prompt,32)
