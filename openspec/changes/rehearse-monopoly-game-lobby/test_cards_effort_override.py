"""Frozen scope and displayed-component checks for the explicit user approval."""
import json
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport, component_label
from test_chat_effort_override import presentation_policy, CHAT
from test_unit_effort_override import TARGET

CARDS='Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyRechargeTests.cs'

def cards_policy(root):
    presentation_policy(root)
    value={'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'stage':'test_authoring','owned_csharp_path':CARDS,
        'effort':'low','explicit_effort_precedence':True}
    (root/'author-cards-effort-policy.json').write_text(json.dumps(value))
    return value

def test_cards_scope_and_component_label_preserve_other_policies(tmp_path,capsys):
    cards_policy(tmp_path);seen=[]
    def send(url,key,payload,timeout):seen.append((payload,timeout));return {'choices':[]}
    base={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,
        'temperature':0,'provider':{'only':['alibaba'],'allow_fallbacks':False}}
    with patch('rehearsal_model_transport.send_chat',send):
        for stage,path,explicit in [('test_authoring',CARDS,None),
                ('test_authoring',CHAT,None),('test_authoring',TARGET,None),
                ('test_authoring','Other.cs',None),('green',CARDS,None),
                ('test_authoring',CARDS,{'effort':'medium'})]:
            payload=base|{'messages':[{'content':'task\n'+json.dumps({'stage':stage,'owns':[path]})}]}
            if explicit:payload['reasoning']=explicit
            RehearsalTransport(tmp_path,'coder')('unused','do-not-display-key',payload,180)
    assert [p['reasoning']['effort'] for p,t in seen]==['low','low','low','none','none','medium']
    assert all(t==180 and p['model']==base['model'] and p['provider']==base['provider']
        and p['temperature']==0 and p['max_completion_tokens']==65536 for p,t in seen)
    output=capsys.readouterr().out
    assert 'Coder (DS4.1 Flash, low)' in output and 'Coder (DS4.1 Flash, none)' in output
    assert 'do-not-display-key' not in output

@pytest.mark.parametrize('field,value',[('effort','high'),('owned_csharp_path','Other.cs')])
def test_cards_policy_rejects_unapproved_values(tmp_path,field,value):
    policy=cards_policy(tmp_path);policy[field]=value
    (tmp_path/'author-cards-effort-policy.json').write_text(json.dumps(policy))
    with patch('rehearsal_model_transport.send_chat') as send:
        with pytest.raises(ValueError):
            RehearsalTransport(tmp_path,'coder')('unused','secret',
                {'model':'deepseek/deepseek-v4.1-flash','messages':[]},180)
        send.assert_not_called()

def test_judge_label_includes_model_and_effort():
    assert component_label('judge','openai/gpt-6.1-sol','medium')=='Judge (GPT-6.1 Sol, medium)'
