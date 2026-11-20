"""Frozen offline checks for the explicitly selected judge's JSON mode."""
from copy import deepcopy
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport


@pytest.mark.parametrize('role,model,expected',[
    ('judge','z-ai/glm-5.3-flash',True),
    ('judge','openai/gpt-6-astra',False),
    ('coder','deepseek/deepseek-v4.1-flash',False),
    ('coder','z-ai/glm-5.3-flash',False),
])
def test_json_mode_is_scoped_without_changing_model_policy(tmp_path,role,model,expected):
    payload={'model':model,'max_completion_tokens':32768,'reasoning':{'effort':'medium'},
        'provider':{'require_parameters':True,'allow_fallbacks':False},
        'messages':[{'role':'user','content':'Return ONLY JSON with valid and explanation.'}]}
    original=deepcopy(payload);seen=[]
    with patch('rehearsal_model_transport.send_chat',lambda url,key,request,timeout: seen.append(request) or {'choices':[]}):
        RehearsalTransport(tmp_path,role)('unused','secret',payload,180)
    assert payload==original
    assert seen[0].get('response_format')==({'type':'json_object'} if expected else None)
    assert {k:v for k,v in seen[0].items() if k!='response_format'}==original


def test_explicit_stricter_format_is_preserved(tmp_path):
    schema={'type':'json_schema','json_schema':{'name':'judge','strict':True,'schema':{'type':'object'}}}
    payload={'model':'z-ai/glm-5.3-flash','max_completion_tokens':32768,
        'provider':{'allow_fallbacks':False},'response_format':schema,'messages':[]}
    seen=[]
    with patch('rehearsal_model_transport.send_chat',lambda url,key,request,timeout: seen.append(request) or {'choices':[]}):
        RehearsalTransport(tmp_path,'judge')('unused','secret',payload,180)
    assert seen[0]['response_format']==schema
