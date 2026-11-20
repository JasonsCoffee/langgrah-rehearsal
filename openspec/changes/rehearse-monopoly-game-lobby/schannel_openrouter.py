"""Target-local Windows TLS transport; one send, verified certificates, no redirect."""
import json
import re
import subprocess
from urllib.parse import urlsplit
from unity_coder.core.ai_models import ModelError


def send_schannel_openrouter(url: str, key: str, payload: dict, timeout: float) -> dict:
    endpoint=urlsplit(url)
    if (endpoint.scheme!='https' or endpoint.hostname!='openrouter.ai'
        or endpoint.port not in (None,443) or endpoint.username or endpoint.password
        or endpoint.query or endpoint.fragment or endpoint.path!='/api/v1/chat/completions'):
        raise ModelError('Unexpected OpenRouter endpoint')
    # curl config reads sensitive headers and JSON through stdin, never argv,
    # environment or a temporary credential file. JSON escaping is also valid
    # curl quoted-config escaping for these header/data strings.
    values={'url':url,'request':'POST','header':'Authorization: Bearer '+key}
    lines=[name+' = '+json.dumps(value,ensure_ascii=False) for name,value in values.items()]
    for header in ('Content-Type: application/json','Accept: application/json','User-Agent: LangGraph-Lobby-Rehearsal/1.0'):
        lines.append('header = '+json.dumps(header))
    lines.append('data-binary = '+json.dumps(json.dumps(payload,ensure_ascii=False),ensure_ascii=False))
    args=['curl.exe','--config','-','--silent','--show-error','--fail-with-body',
          '--proto','=https','--tlsv1.2','--tls-max','1.3','--ssl-revoke-best-effort',
          '--connect-timeout','15','--max-time',str(min(timeout,180)),
          '--write-out','\n%{http_code}']
    try:
        result=subprocess.run(args,input=('\n'.join(lines)+'\n').encode('utf-8'),
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=min(timeout,180)+5,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except subprocess.TimeoutExpired:
        raise ModelError('Schannel request timed out; no automatic retry',diagnostics={'transport':'schannel','failure_kind':'timeout'}) from None
    except OSError:
        raise ModelError('Schannel process unavailable; no automatic retry',diagnostics={'transport':'schannel','failure_kind':'launch'}) from None
    raw,separator,status=result.stdout.rpartition(b'\n')
    details={'transport':'schannel'}
    if separator and status.isdigit() and 100<=int(status)<=599:details['http_status']=int(status)
    if result.returncode:details['curl_exit_code']=result.returncode
    if result.returncode or details.get('http_status')!=200:
        try:
            metadata=json.loads(raw).get('error',{}).get('metadata',{})
            for field in ('provider_name','limit_source'):
                value=metadata.get(field)
                if isinstance(value,str) and key not in value and re.fullmatch(r'[A-Za-z0-9_ ./-]{1,100}',value):details[field]=value
        except (ValueError,AttributeError,TypeError):pass
        raise ModelError('Schannel OpenRouter request failed; no automatic retry',diagnostics=details)
    try:
        if len(raw)>4000000:raise ValueError('size')
        data=json.loads(raw)
        if not isinstance(data,dict):raise ValueError('shape')
    except ValueError:
        raise ModelError('Schannel response is invalid; no automatic retry',diagnostics=details|{'failure_kind':'response'}) from None
    return data
