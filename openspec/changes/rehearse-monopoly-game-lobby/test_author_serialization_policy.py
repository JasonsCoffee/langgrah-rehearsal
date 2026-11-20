"""Frozen opt-in checks; existing defaults and explicit settings stay intact."""
import json
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport


def policy(tmp_path):
    (tmp_path/'author-serialization-policy.json').write_text(json.dumps({
        'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'non_harness_authoring_effort':'none','explicit_effort_precedence':True}))


def test_opt_in_changes_only_unconfigured_non_harness_authoring(tmp_path):
    policy(tmp_path);seen=[]
    def send(url,key,payload,timeout):seen.append(payload);return {'choices':[]}
    base={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,
        'temperature':0,'provider':{'only':['alibaba'],'allow_fallbacks':False}}
    with patch('rehearsal_model_transport.send_chat',send):
        for name,explicit in [('Test.cs',None),('LobbyHarness.cs',None),('Test.cs',{'effort':'medium'})]:
            payload=base|{'messages':[{'content':'task\n'+json.dumps({'stage':'test_authoring','owns':[name]})}]}
            if explicit:payload['reasoning']=explicit
            RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
    assert [p['reasoning'] for p in seen]==[{'effort':'none'},{'effort':'low'},{'effort':'medium'}]
    assert all(p['model']==base['model'] and p['provider']==base['provider'] and p['temperature']==0 and p['max_completion_tokens']==65536 for p in seen)


def test_unrecognized_author_policy_fails_before_request(tmp_path):
    policy(tmp_path);(tmp_path/'author-serialization-policy.json').write_text('{}')
    payload={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,'provider':{},'messages':[]}
    with patch('rehearsal_model_transport.send_chat') as send:
        with pytest.raises(ValueError):RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
        send.assert_not_called()
