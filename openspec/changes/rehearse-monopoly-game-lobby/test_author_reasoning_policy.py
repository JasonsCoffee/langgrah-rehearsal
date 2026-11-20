"""Offline stage reasoning policy; configured effort always takes precedence."""
import json
from unittest.mock import patch
from rehearsal_model_transport import RehearsalTransport


def test_authoring_uses_supported_low_effort_without_changing_models(tmp_path):
    seen=[]
    def send(url,key,payload,timeout):
        seen.append(payload)
        return {'choices':[]}
    base={'model':'configured-coder','max_completion_tokens':65536,'temperature':0,
          'provider':{'only':['configured-endpoint'],'allow_fallbacks':False}}
    with patch('rehearsal_model_transport.send_chat',send):
        for stage in ('test_authoring','green','refactor'):
            payload=base|{'messages':[{'role':'user','content':'task\n'+json.dumps({'stage':stage,'owns':['Test.cs']})}]}
            RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
        explicit=base|{'reasoning':{'effort':'none'},'messages':[{'role':'user','content':'task\n'+json.dumps({'stage':'test_authoring'})}]}
        RehearsalTransport(tmp_path,'coder')('unused','secret',explicit,180)
    assert [p['reasoning']['effort'] for p in seen]==['low','none','none','none']
    assert all(p['model']==base['model'] and p['provider']==base['provider'] and p['max_completion_tokens']==65536 for p in seen)
