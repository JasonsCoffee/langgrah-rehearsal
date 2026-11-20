"""JSON-mode checks for the explicitly selected Sol judge; prior tests unchanged."""
from copy import deepcopy
from unittest.mock import patch
import pytest
from rehearsal_model_transport import RehearsalTransport


@pytest.mark.parametrize('role,model,enabled',[
    ('judge','openai/gpt-6.1-sol',True),
    ('coder','deepseek/deepseek-v4.1-flash',False),
    ('coder','openai/gpt-6.1-sol',False),
])
def test_sol_json_mode_preserves_configured_identity_and_effort(tmp_path,role,model,enabled):
    payload={'model':model,'reasoning':{'effort':'medium'},'max_completion_tokens':32768,
        'provider':{'require_parameters':True,'allow_fallbacks':False},'messages':[]}
    original=deepcopy(payload);sent=[]
    with patch('rehearsal_model_transport.send_chat',lambda url,key,body,timeout:sent.append(body) or {'choices':[]}):
        RehearsalTransport(tmp_path,role)('unused','secret',payload,180)
    assert payload==original
    assert sent[0].get('response_format')==({'type':'json_object'} if enabled else None)
    assert {k:v for k,v in sent[0].items() if k!='response_format'}==original
