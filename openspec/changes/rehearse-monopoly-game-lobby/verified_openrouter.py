"""Target-only verified TLS compatibility; no retries or parser relaxation."""
import json
import re
import ssl
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request,HTTPSHandler,HTTPRedirectHandler,build_opener
from unity_coder.core.ai_models import ModelError


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ModelError('OpenRouter redirect refused')


def send_verified_openrouter(url: str, key: str, payload: dict, timeout: float) -> dict:
    endpoint=urlsplit(url)
    if (endpoint.scheme!='https' or endpoint.hostname!='openrouter.ai'
        or endpoint.port not in (None,443) or endpoint.username or endpoint.password
        or endpoint.query or endpoint.fragment or endpoint.path!='/api/v1/chat/completions'):
        raise ModelError('Unexpected OpenRouter endpoint',diagnostics={'input_tokens':0,'output_tokens':0})
    context=ssl.create_default_context()
    context.minimum_version=context.maximum_version=ssl.TLSVersion.TLSv1_2
    request=Request(url,data=json.dumps(payload).encode(),method='POST',headers={
        'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json',
        'User-Agent':'LangGraph-Lobby-Rehearsal/1.0'})
    try:
        with build_opener(NoRedirect(),HTTPSHandler(context=context)).open(request,timeout=timeout) as response:
            raw=response.read(4000001)
            if len(raw)>4000000:raise ModelError('Model response exceeds size limit')
            result=json.loads(raw)
            if not isinstance(result,dict):raise ModelError('Invalid model response object')
            return result
    except HTTPError as error:
        details={'http_status':error.code}
        retry=error.headers.get('Retry-After','') if error.headers else ''
        if retry.isdigit():details['retry_after_seconds']=min(int(retry),86400)
        try:
            metadata=json.loads(error.read(16384)).get('error',{}).get('metadata',{})
            for field in ('provider_name','limit_source'):
                value=metadata.get(field)
                if isinstance(value,str) and key not in value and re.fullmatch(r'[A-Za-z0-9_ ./-]{1,100}',value):details[field]=value
        except (ValueError,AttributeError,TypeError,OSError):pass
        raise ModelError('Model provider HTTP '+str(error.code),diagnostics=details) from None
    except ModelError:raise
    except (OSError,ValueError):
        raise ModelError('Verified TLS model connection or response failed; no automatic retry') from None
