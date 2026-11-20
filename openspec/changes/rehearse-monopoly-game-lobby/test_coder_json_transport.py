"""Frozen serialization checks for the configured coder's required JSON wire."""
import json
from unittest.mock import patch
from rehearsal_model_transport import RehearsalTransport


def test_configured_coder_requests_json_and_preserves_stricter_format(tmp_path):
    seen=[]
    def send(url,key,payload,timeout):seen.append(payload);return {'choices':[]}
    base={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,'provider':{'only':['alibaba'],'allow_fallbacks':False},
        'messages':[{'content':'task\n'+json.dumps({'stage':'test_authoring','owns':['Test.cs']})}]}
    strict={'type':'json_schema','json_schema':{'name':'provided'}}
    with patch('rehearsal_model_transport.send_chat',send):
        RehearsalTransport(tmp_path,'coder')('unused','secret',base,180)
        RehearsalTransport(tmp_path,'coder')('unused','secret',base|{'response_format':strict},180)
    assert seen[0]['response_format']=={'type':'json_object'}
    assert seen[1]['response_format']==strict
    assert all(p['model']==base['model'] and p['provider']==base['provider'] and p['max_completion_tokens']==65536 for p in seen)
