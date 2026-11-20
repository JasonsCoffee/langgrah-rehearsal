"""Frozen checks for the rehearsal's verified OpenRouter compatibility wire."""
import io
import json
import ssl
from unittest.mock import patch
from urllib.error import HTTPError,URLError
import pytest
from unity_coder.core.ai_models import ModelError


def module():
    import verified_openrouter
    return verified_openrouter


def test_verified_tls12_request_preserves_payload_and_credentials_in_memory():
    m=module();seen={}
    class Reply(io.BytesIO):
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
    class Opener:
        def open(self,request,timeout):
            seen.update(request=request,timeout=timeout)
            return Reply(b'{"choices":[],"usage":{}}')
    def build(*handlers):seen['handlers']=handlers;return Opener()
    payload={'model':'configured','provider':{'allow_fallbacks':False},'reasoning':{'effort':'medium'}}
    with patch.object(m,'build_opener',build):
        assert m.send_verified_openrouter('https://openrouter.ai/api/v1/chat/completions','secret-key',payload,180)=={'choices':[],'usage':{}}
    handler=next(h for h in seen['handlers'] if hasattr(h,'_context'));context=handler._context
    assert context.check_hostname and context.verify_mode==ssl.CERT_REQUIRED
    assert context.minimum_version==context.maximum_version==ssl.TLSVersion.TLSv1_2
    assert json.loads(seen['request'].data)==payload
    assert seen['request'].get_header('Authorization')=='Bearer secret-key'
    assert seen['request'].get_header('User-agent')=='LangGraph-Lobby-Rehearsal/1.0'
    assert seen['timeout']==180
    redirect=next(h for h in seen['handlers'] if hasattr(h,'redirect_request'))
    with pytest.raises(ModelError):redirect.redirect_request(None,None,302,'',{},'https://elsewhere.invalid')


@pytest.mark.parametrize('kind',['tls','invalid_json','oversize','http'])
def test_wire_fails_closed_without_retries_or_credential_diagnostics(kind):
    m=module();attempts=[]
    class Reply(io.BytesIO):
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
    class Opener:
        def open(self,request,timeout):
            attempts.append(request)
            if kind=='tls':raise URLError(ssl.SSLEOFError('closed'))
            if kind=='http':raise HTTPError(request.full_url,402,'secret-key',{},io.BytesIO(b'{"error":{"metadata":{"limit_source":"openrouter_key_limit"}}}'))
            return Reply(b'x'*4000001 if kind=='oversize' else b'not-json secret-key')
    with patch.object(m,'build_opener',lambda *args:Opener()):
        with pytest.raises(ModelError) as error:m.send_verified_openrouter('https://openrouter.ai/api/v1/chat/completions','secret-key',{},10)
    assert len(attempts)==1
    assert 'secret-key' not in str(error.value)+json.dumps(error.value.diagnostics)
    if kind=='http':assert error.value.diagnostics=={'http_status':402,'limit_source':'openrouter_key_limit'}


def test_foreign_endpoint_is_rejected_before_sending_credentials():
    m=module()
    with patch.object(m,'build_opener') as build:
        with pytest.raises(ModelError):m.send_verified_openrouter('https://elsewhere.invalid/chat','secret-key',{},10)
    build.assert_not_called()
