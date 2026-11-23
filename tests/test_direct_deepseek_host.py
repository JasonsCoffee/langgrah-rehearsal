"""Direct-provider behavior; no network or local credentials required."""
import json
from pathlib import Path
import sys
import pytest
from unity_coder.core.ai_models import ModelError

HOST=Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()
sys.path.insert(0,str(HOST))


def client(transport):
    from direct_deepseek_client import DirectDeepSeekClient
    return DirectDeepSeekClient('private-test-key',transport=transport)


def response(**changes):
    return {'id':'reply','model':'deepseek-flash','choices':[{'finish_reason':'stop','message':{'content':'{"files":{},"reason":"done"}'}}],
        'usage':{'prompt_tokens':25,'completion_tokens':8,'prompt_cache_hit_tokens':10},**changes}


def test_direct_dialect_explicit_low_and_json_without_router_fields():
    seen=[]
    def send(url,key,payload,timeout):seen.append((url,key,payload,timeout));return response()
    c=client(send);r=c.generate('produce JSON',max_output_tokens=65536)
    url,key,p,t=seen[0]
    assert url=='https://api.deepseek.com/chat/completions' and key=='private-test-key'
    assert p['thinking']=={'type':'enabled'} and p['reasoning_effort']=='low' and p['max_tokens']==65536
    assert p['response_format']=={'type':'json_object'}
    assert not set(p)&{'provider','reasoning','temperature','tools','max_completion_tokens'}
    assert (r.input_tokens,r.output_tokens)==(25,8) and c.config.provider=='deepseek'
    assert 'private-test-key' not in repr(c.config)


@pytest.mark.parametrize('bad',['length','reasoning_only','model','invalid_json','bad_usage'])
def test_invalid_outputs_never_become_patches_and_report_known_usage(bad):
    d=response()
    if bad=='length':d['choices'][0]['finish_reason']='length'
    if bad=='reasoning_only':d['choices'][0]['message']={'content':'','reasoning_content':'private thoughts'}
    if bad=='model':d['model']='unexpected'
    if bad=='invalid_json':d['choices'][0]['message']['content']='not JSON'
    if bad=='bad_usage':d['usage']['completion_tokens']=True
    with pytest.raises(ModelError) as error:client(lambda *args:d).generate('JSON',max_output_tokens=32)
    if bad!='bad_usage':assert error.value.diagnostics['input_tokens']==25
    assert 'private thoughts' not in str(error.value.diagnostics)


def test_unknown_submission_error_has_no_fabricated_zero_usage():
    def send(*args):raise TimeoutError('key private-test-key payload')
    with pytest.raises(ModelError) as error:client(send).generate('JSON',max_output_tokens=32)
    assert 'input_tokens' not in error.value.diagnostics and 'private-test-key' not in str(error.value)


def test_missing_local_key_and_unapproved_endpoint_fail_before_dispatch(tmp_path):
    from direct_deepseek_client import load_direct_config,DirectDeepSeekClient
    path=tmp_path/'ai.local.toml';path.write_text('[coder]\nprovider="deepseek"\napi_key=""\nmodel="deepseek-flash"\neffort="low"\nbase_url="https://api.deepseek.com"\n')
    with pytest.raises(ModelError):load_direct_config(path)
    with pytest.raises(ModelError):DirectDeepSeekClient('key',endpoint='https://unapproved.invalid')


def test_known_truncation_usage_is_charged_by_native_ledger(tmp_path):
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.model_calls import ModelCalls
    ledger=BudgetLedger(tmp_path,'run',input_limit=100000,output_limit=100000,max_cycles=2,max_added_units=2)
    ledger.begin_cycle(1,'contract',{'U':('U',)})
    d=response();d['choices'][0]['finish_reason']='length'
    with pytest.raises(ModelError):ModelCalls(client(lambda *args:d),ledger,'run').generate('call','U','JSON',max_output_tokens=32)
    assert ledger.totals()==(25,8)
