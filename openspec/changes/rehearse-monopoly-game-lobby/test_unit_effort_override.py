"""Frozen scope/precedence checks for a dormant operator-approved unit override."""
import json
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport


TARGET='Tests/Runtime/Script/LobbyRehearsal/LobbyChatMessageTests.cs'


def setup_policy(root):
    (root/'author-serialization-policy.json').write_text(json.dumps({
        'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'non_harness_authoring_effort':'none','explicit_effort_precedence':True}))
    value={'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'stage':'test_authoring','owned_csharp_path':TARGET,
        'effort':'low','explicit_effort_precedence':True}
    (root/'author-unit-effort-policy.json').write_text(json.dumps(value))
    return value


def test_unit_override_preserves_other_roles_stages_and_explicit_settings(tmp_path):
    setup_policy(tmp_path);seen=[]
    def send(url,key,payload,timeout):seen.append((payload,timeout));return {'choices':[]}
    base={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,
        'temperature':0,'provider':{'only':['alibaba'],'allow_fallbacks':False}}
    cases=[('test_authoring',TARGET,None),('test_authoring','Other.cs',None),
        ('green',TARGET,None),('test_authoring','LobbyHarness.cs',None),
        ('test_authoring',TARGET,{'effort':'medium'})]
    with patch('rehearsal_model_transport.send_chat',send):
        for stage,path,explicit in cases:
            payload=base|{'messages':[{'content':'task\n'+json.dumps({'stage':stage,'owns':[path]})}]}
            if explicit:payload['reasoning']=explicit
            RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
        judge=base|{'model':'openai/gpt-6.1-sol','reasoning':{'effort':'medium'},
            'messages':[{'content':'task\n'+json.dumps({'stage':'test_authoring','owns':[TARGET]})}]}
        RehearsalTransport(tmp_path,'judge')('unused','secret',judge,180)
    assert [p['reasoning'] for p,t in seen]==[{'effort':'low'},{'effort':'none'},
        {'effort':'none'},{'effort':'low'},{'effort':'medium'},{'effort':'medium'}]
    assert all(t==180 and p['max_completion_tokens']==65536 and p['temperature']==0
        and p['provider']==base['provider'] for p,t in seen)
    assert [p['model'] for p,t in seen]==[base['model']]*5+['openai/gpt-6.1-sol']


@pytest.mark.parametrize('field,value',[('effort','medium'),('owned_csharp_path','Other.cs')])
def test_unknown_unit_override_is_rejected_before_send(tmp_path,field,value):
    policy=setup_policy(tmp_path);policy[field]=value
    (tmp_path/'author-unit-effort-policy.json').write_text(json.dumps(policy))
    payload={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,
        'provider':{},'messages':[]}
    with patch('rehearsal_model_transport.send_chat') as send:
        with pytest.raises(ValueError):RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
        send.assert_not_called()
