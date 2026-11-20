"""Direct TLS setup recovery before sending one authenticated HTTP request."""
from http.client import HTTPSConnection,HTTPException
import json
import re
import ssl
import time
from urllib.parse import urlsplit
from unity_coder.core.ai_models import ModelError


def send_preconnected_openrouter(url: str, key: str, payload: dict, timeout: float) -> dict:
    endpoint=urlsplit(url)
    if (endpoint.scheme!='https' or endpoint.hostname!='openrouter.ai'
        or endpoint.port not in (None,443) or endpoint.username or endpoint.password
        or endpoint.query or endpoint.fragment or endpoint.path!='/api/v1/chat/completions'):
        raise ModelError('Unexpected OpenRouter endpoint')
    context=ssl.create_default_context();context.minimum_version=ssl.TLSVersion.TLSv1_2
    deadline=time.monotonic()+min(timeout,180);connection=None
    for attempt in range(3):
        connection=HTTPSConnection('openrouter.ai',timeout=min(8,max(.01,deadline-time.monotonic())),context=context)
        try:
            # No HTTP bytes, credentials or model payload are sent here.
            connection.connect()
            break
        except ssl.SSLCertVerificationError:
            connection.close()
            raise ModelError('Direct certificate verification failed',diagnostics={
                'transport':'direct_preconnect','phase':'tls_establishment','failure_kind':'certificate',
                'input_tokens':0,'output_tokens':0}) from None
        except OSError as error:
            connection.close()
            if attempt==2 or time.monotonic()>=deadline:
                raise ModelError('Direct TLS establishment failed before HTTP',diagnostics={
                    'transport':'direct_preconnect','phase':'tls_establishment',
                    'failure_kind':'tls' if isinstance(error,ssl.SSLError) else 'connection',
                    'input_tokens':0,'output_tokens':0}) from None
            time.sleep(min(1+2*attempt,max(0,deadline-time.monotonic())))
    try:
        request_stage='send'
        # Do not let http.client establish another connection after sending
        # begins. Any subsequent failure has unknown paid effects and stops.
        connection.auto_open=0
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError()
        connection.sock.settimeout(remaining)
        connection.request('POST',endpoint.path,json.dumps(payload,ensure_ascii=False).encode('utf-8'),{
            'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json',
            'User-Agent':'LangGraph-Lobby-Rehearsal/1.0'})
        request_stage='headers';response=connection.getresponse()
        request_stage='body';raw=response.read(4000001)
        details={'transport':'direct_preconnect','http_status':response.status}
        if response.status!=200:
            retry=response.getheader('Retry-After','')
            if retry.isdigit():details['retry_after_seconds']=min(int(retry),86400)
            try:
                metadata=json.loads(raw).get('error',{}).get('metadata',{})
                for field in ('provider_name','limit_source'):
                    value=metadata.get(field)
                    if isinstance(value,str) and key not in value and re.fullmatch(r'[A-Za-z0-9_ ./-]{1,100}',value):details[field]=value
            except (ValueError,AttributeError,TypeError):pass
            raise ModelError('OpenRouter HTTP request failed; no retry',diagnostics=details)
        if len(raw)>4000000:raise ValueError('size')
        request_stage='decode';data=json.loads(raw)
        if not isinstance(data,dict):raise ValueError('shape')
        return data
    except ModelError:raise
    except (OSError,HTTPException,ValueError) as error:
        kind=('tls' if isinstance(error,ssl.SSLError) else 'timeout' if isinstance(error,TimeoutError)
            else 'http_protocol' if isinstance(error,HTTPException) else 'invalid_response' if isinstance(error,ValueError)
            else 'connection')
        raise ModelError('Direct request or response failed after TLS setup; no retry',diagnostics={
            'transport':'direct_preconnect','phase':'request','failure_kind':kind,'request_stage':request_stage}) from None
    finally:connection.close()
