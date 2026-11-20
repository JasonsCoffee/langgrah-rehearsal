"""Frozen no-duplicate-request checks for direct TLS establishment recovery."""
import io
import json
import ssl
from unittest.mock import patch
import pytest
from unity_coder.core.ai_models import ModelError


def run_wire(connect_failures=0,post_failure=False,certificate=False,status=200):
    import preconnected_openrouter as m
    seen={'connections':0,'requests':[],'closed':0,'contexts':[]}
    class Response(io.BytesIO):
        def __init__(self):super().__init__(b'{"choices":[],"usage":{}}')
        def getheader(self,name,default=None):return default
    class Socket:
        def settimeout(self,value):assert 0<value<=180
    class Connection:
        def __init__(self,host,timeout,context):
            assert host=='openrouter.ai';seen['connections']+=1;seen['contexts'].append(context)
            self.sock=Socket();self.auto_open=1
        def connect(self):
            if certificate:raise ssl.SSLCertVerificationError('private detail')
            if seen['connections']<=connect_failures:raise ssl.SSLEOFError('closed')
        def request(self,method,path,body,headers):
            assert self.auto_open==0
            seen['requests'].append((method,path,json.loads(body),headers))
            if post_failure:raise TimeoutError('private detail')
        def getresponse(self):
            response=Response();response.status=status;return response
        def close(self):seen['closed']+=1
    with patch.object(m,'HTTPSConnection',Connection):
        try:result=m.send_preconnected_openrouter('https://openrouter.ai/api/v1/chat/completions','secret-key',{'model':'configured','text':'中文\n"quoted"'},180)
        except ModelError as error:return seen,error
    return seen,result


def test_only_tls_establishment_retries_before_one_paid_request():
    seen,result=run_wire(connect_failures=2)
    assert result=={'choices':[],'usage':{}}
    assert seen['connections']==3 and len(seen['requests'])==1
    method,path,body,headers=seen['requests'][0]
    assert method=='POST' and path=='/api/v1/chat/completions'
    assert body=={'model':'configured','text':'中文\n"quoted"'}
    assert headers['Authorization']=='Bearer secret-key'
    assert all(c.check_hostname and c.verify_mode==ssl.CERT_REQUIRED for c in seen['contexts'])


def test_failed_post_never_reconnects_or_retries_and_keeps_unknown_usage():
    seen,error=run_wire(post_failure=True)
    assert seen['connections']==1 and len(seen['requests'])==1
    assert error.diagnostics['phase']=='request'
    assert 'input_tokens' not in error.diagnostics
    assert 'secret-key' not in str(error)+json.dumps(error.diagnostics)


def test_all_handshakes_fail_without_transmitting_http_or_credentials():
    seen,error=run_wire(connect_failures=3)
    assert seen['connections']==3 and seen['requests']==[]
    assert error.diagnostics['phase']=='tls_establishment'
    assert error.diagnostics['input_tokens']==error.diagnostics['output_tokens']==0
    assert seen['closed']==3


def test_certificate_failure_is_final_before_request():
    seen,error=run_wire(certificate=True)
    assert seen['connections']==1 and not seen['requests']
    assert error.diagnostics['failure_kind']=='certificate'


@pytest.mark.parametrize('status',[302,402])
def test_no_redirect_or_http_retry(status):
    seen,error=run_wire(status=status)
    assert len(seen['requests'])==1 and error.diagnostics['http_status']==status
    assert 'input_tokens' not in error.diagnostics


def test_foreign_destination_rejected_before_connection():
    import preconnected_openrouter as m
    with patch.object(m,'HTTPSConnection') as connect:
        with pytest.raises(ModelError):m.send_preconnected_openrouter('https://elsewhere.invalid/chat','secret-key',{},180)
        connect.assert_not_called()
