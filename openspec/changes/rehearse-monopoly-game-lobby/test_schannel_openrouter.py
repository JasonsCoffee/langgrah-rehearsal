"""Frozen checks for credential-safe native Windows TLS, without paid retries."""
import json
import subprocess
from unittest.mock import patch
import pytest
from unity_coder.core.ai_models import ModelError


def test_native_wire_keeps_key_off_command_line_and_preserves_json():
    import schannel_openrouter as m
    seen={}
    payload={'model':'configured','messages':[{'content':'line1\n"quoted"\\path 中文'}]}
    def run(args,**kwargs):
        seen.update(args=args,**kwargs)
        return subprocess.CompletedProcess(args,0,b'{"choices":[],"usage":{}}\n200',b'')
    with patch.object(m.subprocess,'run',run):
        assert m.send_schannel_openrouter('https://openrouter.ai/api/v1/chat/completions','secret-key',payload,180)=={'choices':[],'usage':{}}
    assert 'secret-key' not in repr(seen['args'])
    assert '--insecure' not in seen['args'] and '-k' not in seen['args']
    assert '--ssl-revoke-best-effort' in seen['args']
    assert '--retry' not in seen['args'] and '--location' not in seen['args']
    config=seen['input'].decode('utf-8')
    assert 'Authorization: Bearer secret-key' in config
    data=next(line.split(' = ',1)[1] for line in config.splitlines() if line.startswith('data-binary = '))
    assert json.loads(json.loads(data))==payload
    assert seen['timeout']<=185 and not seen.get('shell',False)


@pytest.mark.parametrize('kind',['tls','timeout','http','invalid_json','redirect'])
def test_failures_never_retry_or_expose_credentials(kind):
    import schannel_openrouter as m
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        if kind=='timeout':raise subprocess.TimeoutExpired(args,180)
        if kind=='tls':return subprocess.CompletedProcess(args,35,b'\n000',b'secret-key')
        if kind=='http':return subprocess.CompletedProcess(args,22,b'{"error":{}}\n402',b'secret-key')
        if kind=='redirect':return subprocess.CompletedProcess(args,0,b'{}\n302',b'')
        return subprocess.CompletedProcess(args,0,b'secret-key\n200',b'')
    with patch.object(m.subprocess,'run',run):
        with pytest.raises(ModelError) as error:m.send_schannel_openrouter('https://openrouter.ai/api/v1/chat/completions','secret-key',{},180)
    assert len(calls)==1
    assert 'secret-key' not in str(error.value)+json.dumps(error.value.diagnostics)
    assert 'input_tokens' not in error.value.diagnostics
    if kind=='http':assert error.value.diagnostics['http_status']==402
    if kind=='tls':assert error.value.diagnostics['curl_exit_code']==35


def test_foreign_endpoint_never_receives_key():
    import schannel_openrouter as m
    with patch.object(m.subprocess,'run') as run:
        with pytest.raises(ModelError):m.send_schannel_openrouter('https://elsewhere.invalid/chat','secret-key',{},180)
        run.assert_not_called()
