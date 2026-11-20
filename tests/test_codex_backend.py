"""Offline acceptance for an opt-in Codex backend; no subscription calls."""
from hashlib import sha256
import json
from pathlib import Path

import pytest
from test_ai_models import config, response
from unity_coder.core.ai_models import ModelClient, ModelError, load_ai_config
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.model_calls import ModelCalls


def backend(tmp_path, *, role='coder', mode='dispatch_accounting', approved=True, events=None, max_calls=1):
    from unity_coder.core.codex_backend import CodexModelClient, CodexPolicy
    work=tmp_path/'worker';work.mkdir(exist_ok=True)
    policy=CodexPolicy(role=role,model='model-'+role,effort='low' if role=='coder' else 'medium',
        budget_mode=mode,authorization_ref='approvals/explicit.json',max_calls=max_calls)
    seen=[]
    def exchange(request):
        seen.append(request)
        return events if events is not None else turn_events()
    client=CodexModelClient(policy,tmp_path/'state',work,exchange=exchange,authorize=lambda digest:approved)
    ledger=BudgetLedger(tmp_path/'state','run',input_limit=100000,output_limit=10000,max_cycles=3,max_added_units=2)
    ledger.begin_cycle(1,'contract',{'A':('A',)})
    return client,ModelCalls(client,ledger,'run'),ledger,seen


def turn_events():
    return [
        {'method':'thread/tokenUsage/updated','params':{'threadId':'thread','turnId':'turn','tokenUsage':{'total':{
            'inputTokens':50,'cachedInputTokens':10,'outputTokens':12,'reasoningOutputTokens':5,'totalTokens':62}}}},
        {'method':'item/completed','params':{'threadId':'thread','turnId':'turn','item':{
            'type':'agentMessage','id':'message','phase':'final_answer','text':'{"files":{},"reason":"reviewable"}'}}},
        {'method':'turn/completed','params':{'threadId':'thread','turn':{'id':'turn','status':'completed'}}},
    ]


def test_strict_budget_default_blocks_before_reserving_or_dispatching(tmp_path):
    _,calls,ledger,seen=backend(tmp_path,mode='require_hard_caps')
    with pytest.raises(ModelError,match='hard.*cap'):calls.generate('call','A','contract',max_output_tokens=64)
    assert ledger.totals()==(0,0) and not ledger._read()['calls'] and not seen


def test_dispatch_accounting_requires_explicit_authorization_before_reservation(tmp_path):
    _,calls,ledger,seen=backend(tmp_path,approved=False)
    with pytest.raises(ModelError,match='authorization'):calls.generate('call','A','contract',max_output_tokens=64)
    assert ledger.totals()==(0,0) and not seen


def test_native_ledger_settles_actual_usage_and_replay_does_not_start_another_agent(tmp_path):
    client,calls,ledger,seen=backend(tmp_path)
    first=calls.generate('call','A','same approved contract',max_output_tokens=64)
    assert (first.input_tokens,first.output_tokens)==(50,12)
    assert calls.generate('call','A','same approved contract',max_output_tokens=64)==first
    assert len(seen)==1 and ledger.totals()==(50,12)
    request=seen[0]
    assert request['operation_id']=='call' and request['role']=='coder'
    assert request['sandbox']=='read-only' and request['tools_enabled'] is False
    assert request['fresh_context'] is True and request['model']=='model-coder'
    assert request['output_allocation']==64 and request['budget_enforcement']=='dispatch_accounting'
    assert request['input_allocation']>len(request['prompt'].encode())+1024
    receipt=json.loads(next((client.state/'codex-receipts').glob('*.json')).read_bytes())
    assert receipt['thread_id']=='thread' and receipt['turn_id']=='turn'
    assert 'reasoning' not in receipt and receipt['policy_sha256']==client.policy.sha256


def test_existing_openrouter_receipts_and_reservations_are_compatible(tmp_path):
    settings=load_ai_config(config(tmp_path));seen=[]
    client=ModelClient(settings.coder,transport=lambda *args:seen.append(1) or response())
    ledger=BudgetLedger(tmp_path/'state','run',input_limit=10000,output_limit=1000,max_cycles=3,max_added_units=2)
    ledger.begin_cycle(1,'contract',{'A':('A',)})
    calls=ModelCalls(client,ledger,'run');reply=calls.generate('original','A','Code',max_output_tokens=64)
    receipt=next((tmp_path/'state/.agent/runs/run/model-calls').glob('*.json'))
    original=json.loads(receipt.read_bytes())
    assert 'worker_backend' not in original['identity']
    assert ledger._read()['calls']['original']['reserved']==[1028,64]
    assert calls.generate('original','A','Code',max_output_tokens=64)==reply and len(seen)==1


def test_changed_backend_identity_cannot_reuse_old_call_id(tmp_path):
    _,calls,ledger,seen=backend(tmp_path)
    calls.generate('call','A','contract',max_output_tokens=64)
    from unity_coder.core.codex_backend import CodexModelClient, CodexPolicy
    policy=CodexPolicy(role='coder',model='different-model',effort='low',budget_mode='dispatch_accounting',
        authorization_ref='approvals/explicit.json',max_calls=1)
    other=CodexModelClient(policy,tmp_path/'state',tmp_path/'worker',exchange=lambda req:pytest.fail('no replay'),authorize=lambda _:True)
    with pytest.raises(ModelError,match='identity'):ModelCalls(other,ledger,'run').generate('call','A','contract',max_output_tokens=64)
    assert ledger.totals()==(50,12)


def test_unknown_or_missing_usage_preserves_full_reservation(tmp_path):
    _,calls,ledger,seen=backend(tmp_path,events=turn_events()[1:])
    with pytest.raises(ModelError):calls.generate('call','A','contract',max_output_tokens=64)
    reserved=ledger.totals()
    assert reserved[0]>0 and reserved[1]==64
    with pytest.raises(ModelError):calls.generate('call','A','contract',max_output_tokens=64)
    assert len(seen)==1 and ledger.totals()==reserved


@pytest.mark.parametrize('kind',['commandExecution','fileChange','mcpToolCall','webSearch','collabAgentToolCall'])
def test_tool_effects_are_rejected_and_never_admitted(tmp_path,kind):
    events=[{'method':'item/started','params':{'threadId':'thread','turnId':'turn','item':{'type':kind}}}]+turn_events()
    _,calls,ledger,_=backend(tmp_path,events=events)
    with pytest.raises(ModelError,match='tool'):calls.generate('call','A','contract',max_output_tokens=64)
    assert 'actual' not in ledger._read()['calls']['call']


def test_model_rerouting_is_never_silent(tmp_path):
    events=[{'method':'model/rerouted','params':{'fromModel':'model-coder','toModel':'other'}}]+turn_events()
    _,calls,ledger,_=backend(tmp_path,events=events)
    with pytest.raises(ModelError,match='model'):calls.generate('call','A','contract',max_output_tokens=64)
    assert 'actual' not in ledger._read()['calls']['call']


@pytest.mark.parametrize('bad',['negative','boolean','wrong-total','wrong-thread','duplicate-final','failed-turn'])
def test_inconsistent_usage_or_completion_fails_closed(tmp_path,bad):
    events=turn_events()
    total=events[0]['params']['tokenUsage']['total']
    if bad=='negative':total['inputTokens']=-1
    elif bad=='boolean':total['outputTokens']=True
    elif bad=='wrong-total':total['totalTokens']=1
    elif bad=='wrong-thread':events[1]['params']['threadId']='different'
    elif bad=='duplicate-final':events.insert(2,events[1])
    else:events[-1]['params']['turn']['status']='failed'
    _,calls,_,_=backend(tmp_path,events=events)
    with pytest.raises(ModelError):calls.generate('call','A','contract',max_output_tokens=64)


def test_authorized_claim_limit_is_persistent_and_never_retries_unknown_effects(tmp_path):
    client,calls,ledger,seen=backend(tmp_path)
    calls.generate('one','A','contract',max_output_tokens=64)
    with pytest.raises(ModelError,match='claim'):calls.generate('two','A','another contract',max_output_tokens=64)
    assert len(seen)==1
    assert ledger._read()['calls']['two']['actual']==[0,0]


def test_known_provider_overrun_is_recorded_truthfully(tmp_path):
    events=turn_events();events[0]['params']['tokenUsage']['total'].update(outputTokens=80,totalTokens=130)
    _,calls,ledger,_=backend(tmp_path,events=events)
    with pytest.raises(ModelError,match='allocation'):calls.generate('call','A','contract',max_output_tokens=64)
    assert ledger.totals()==(50,80)


def test_judge_uses_clean_context_and_explicit_different_model(tmp_path):
    _,calls,_,seen=backend(tmp_path,role='judge')
    calls.generate('review','A','canonical requirements and candidate only',max_output_tokens=64)
    assert seen[0]['role']=='judge' and seen[0]['model']=='model-judge'
    assert seen[0]['fresh_context'] and 'canonical requirements' in seen[0]['prompt']


@pytest.mark.parametrize('change',['bad-role','bad-effort','bad-mode','absolute-proof','zero-claims'])
def test_invalid_policy_is_rejected(change):
    from unity_coder.core.codex_backend import CodexPolicy
    data={'role':'coder','model':'model','effort':'low','budget_mode':'dispatch_accounting',
        'authorization_ref':'approvals/explicit.json','max_calls':1}
    if change=='bad-role':data['role']='architect'
    elif change=='bad-effort':data['effort']='invented'
    elif change=='bad-mode':data['budget_mode']='unlimited'
    elif change=='absolute-proof':data['authorization_ref']='/outside/proof'
    else:data['max_calls']=0
    with pytest.raises(ValueError):CodexPolicy(**data)
