"""Frozen routing identity and durable rejected-response accounting."""
import json
from dataclasses import replace
from io import BytesIO
from urllib.error import HTTPError

import pytest
from test_ai_models import config, response
from test_model_calls import setup
from unity_coder.core.ai_models import load_ai_config, ModelClient, ModelError, send_chat


def test_explicit_upstream_pin_keeps_model_temperature_and_no_fallback(tmp_path):
    path=config(tmp_path)
    text=path.read_text().replace('[coder]','[coder]\nupstream_provider="alibaba"')
    path.write_text(text)
    settings=load_ai_config(path)
    seen=[]
    ModelClient(settings.coder,transport=lambda *args:seen.append(args[2]) or response()).generate('code',max_output_tokens=64)
    assert seen[0]['provider']=={'require_parameters':True,'allow_fallbacks':False,'only':['alibaba']}
    assert seen[0]['model']=='coder-model' and seen[0]['temperature']==0


def test_http_failure_is_durable_sanitized_and_never_automatically_replayed(tmp_path,monkeypatch):
    import unity_coder.core.ai_models as module
    count=[]
    class Opener:
        def open(self,*args,**kwargs):
            count.append(1)
            raise HTTPError('https://example.invalid',429,'limited',{'Retry-After':'15'},
                BytesIO(json.dumps({'error':{'message':'private-test-key','metadata':{
                    'provider_name':'Baidu','limit_source':'upstream_provider_shared_pool','raw':'private-test-key'}}}).encode()))
    monkeypatch.setattr(module,'build_opener',lambda *args:Opener())
    calls,budget=setup(tmp_path,send_chat)
    with pytest.raises(ModelError): calls.generate('limited','A','code',max_output_tokens=64)
    saved=json.loads(next((budget.root/calls.prefix).glob('*.json')).read_bytes())
    assert saved['failure']['http_status']==429
    assert saved['failure']['retry_after_seconds']==15
    assert saved['failure']['limit_source']=='upstream_provider_shared_pool'
    assert 'private-test-key' not in json.dumps(saved)
    charged=budget.totals()
    with pytest.raises(ModelError): calls.generate('limited','A','code',max_output_tokens=64)
    assert len(count)==1 and budget.totals()==charged


def test_incomplete_response_retains_partial_content_and_charges_reported_usage(tmp_path):
    raw=response();raw['choices'][0].update(finish_reason='length',message={'content':'{"files":'})
    calls,budget=setup(tmp_path,lambda *args:raw)
    with pytest.raises(ModelError): calls.generate('short','A','code',max_output_tokens=64)
    saved=json.loads(next((budget.root/calls.prefix).glob('*.json')).read_bytes())
    assert saved['failure']['finish_reason']=='length'
    assert saved['failure']['partial_content']=='{"files":'
    assert budget.totals()==(8,2)
    with pytest.raises(ModelError): calls.generate('short','A','code',max_output_tokens=64)
    assert budget.totals()==(8,2)


def test_route_is_part_of_paid_call_identity(tmp_path):
    calls,_=setup(tmp_path,lambda *args:response())
    calls.generate('first','A','code',max_output_tokens=64)
    calls.client.config=replace(calls.client.config,upstream_provider='alibaba')
    with pytest.raises(ModelError,match='identity'):
        calls.generate('first','A','code',max_output_tokens=64)
