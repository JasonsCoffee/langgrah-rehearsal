"""Freeze the separately approved presentation-author scope before wiring it."""
import json
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport
from test_unit_effort_override import setup_policy, TARGET

CHAT='Tests/Runtime/Script/LobbyRehearsal/LobbySocialChatTests.cs'

def presentation_policy(root):
    setup_policy(root)
    value={'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'stage':'test_authoring','owned_csharp_path':CHAT,
        'effort':'low','explicit_effort_precedence':True}
    (root/'author-chat-effort-policy.json').write_text(json.dumps(value))
    return value

def test_presentation_scope_preserves_message_override_and_explicit_effort(tmp_path):
    presentation_policy(tmp_path);seen=[]
    def send(url,key,payload,timeout):seen.append(payload);return {'choices':[]}
    base={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,
        'temperature':0,'provider':{'only':['alibaba'],'allow_fallbacks':False}}
    with patch('rehearsal_model_transport.send_chat',send):
        for stage,path,explicit in [('test_authoring',CHAT,None),
                ('test_authoring',TARGET,None),('test_authoring','State.cs',None),
                ('green',CHAT,None),('test_authoring',CHAT,{'effort':'medium'})]:
            payload=base|{'messages':[{'content':'task\n'+json.dumps({'stage':stage,'owns':[path]})}]}
            if explicit:payload['reasoning']=explicit
            RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
    assert [p['reasoning'] for p in seen]==[{'effort':'low'},{'effort':'low'},
        {'effort':'none'},{'effort':'none'},{'effort':'medium'}]
    assert all(p['model']==base['model'] and p['provider']==base['provider']
        and p['temperature']==0 and p['max_completion_tokens']==65536 for p in seen)

def test_presentation_policy_rejects_other_scope(tmp_path):
    value=presentation_policy(tmp_path);value['owned_csharp_path']='State.cs'
    (tmp_path/'author-chat-effort-policy.json').write_text(json.dumps(value))
    with patch('rehearsal_model_transport.send_chat') as send:
        with pytest.raises(ValueError):
            RehearsalTransport(tmp_path,'coder')('unused','secret',
                {'model':'deepseek/deepseek-v4.1-flash','messages':[]},180)
        send.assert_not_called()
