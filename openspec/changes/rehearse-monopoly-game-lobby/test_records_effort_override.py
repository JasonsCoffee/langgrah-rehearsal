"""Frozen exact Records-only scope for the explicit low-effort approval."""
import json
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport
from test_cards_effort_override import cards_policy, CARDS

RECORDS='Tests/Runtime/Script/LobbyRehearsal/LobbyRecordsSettingsTests.cs'

def records_policy(root):
    cards_policy(root)
    value={'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'stage':'test_authoring','owned_csharp_path':RECORDS,
        'effort':'low','explicit_effort_precedence':True}
    (root/'author-records-effort-policy.json').write_text(json.dumps(value))
    return value

def test_records_only_override_preserves_stage_and_explicit_precedence(tmp_path):
    records_policy(tmp_path);seen=[]
    def send(url,key,payload,timeout):seen.append((payload,timeout));return {'choices':[]}
    base={'model':'deepseek/deepseek-v4.1-flash','max_completion_tokens':65536,
        'temperature':0,'provider':{'only':['alibaba'],'allow_fallbacks':False}}
    with patch('rehearsal_model_transport.send_chat',send):
        for stage,path,explicit in [('test_authoring',RECORDS,None),
                ('test_authoring',CARDS,None),('test_authoring','State.cs',None),
                ('green',RECORDS,None),('refactor',RECORDS,None),
                ('test_authoring',RECORDS,{'effort':'medium'})]:
            payload=base|{'messages':[{'content':'task\n'+json.dumps({'stage':stage,'owns':[path]})}]}
            if explicit:payload['reasoning']=explicit
            RehearsalTransport(tmp_path,'coder')('unused','secret',payload,180)
    assert [p['reasoning']['effort'] for p,t in seen]==['low','low','none','none','none','medium']
    assert all(t==180 and p['model']==base['model'] and p['provider']==base['provider']
        and p['temperature']==0 and p['max_completion_tokens']==65536 for p,t in seen)

@pytest.mark.parametrize('field,value',[('effort','high'),('owned_csharp_path','State.cs')])
def test_records_policy_rejects_unapproved_values(tmp_path,field,value):
    value_policy=records_policy(tmp_path);value_policy[field]=value
    (tmp_path/'author-records-effort-policy.json').write_text(json.dumps(value_policy))
    with patch('rehearsal_model_transport.send_chat') as send:
        with pytest.raises(ValueError):
            RehearsalTransport(tmp_path,'coder')('unused','secret',
                {'model':'deepseek/deepseek-v4.1-flash','messages':[]},180)
        send.assert_not_called()
