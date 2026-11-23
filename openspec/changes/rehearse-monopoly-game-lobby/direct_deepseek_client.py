"""Direct DeepSeek dialect behind the existing paid-call boundary."""
from __future__ import annotations
from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
import ssl
import tomllib
from urllib.error import HTTPError
from urllib.request import Request,HTTPRedirectHandler,HTTPSHandler,ProxyHandler,build_opener
from unity_coder.core.ai_models import ModelClient,ModelConfig,ModelReply,ModelError,Transport
from unity_coder.core.storage import atomic_write


ENDPOINT='https://api.deepseek.com'
ACCEPTED_MODELS=frozenset(('deepseek-flash','deepseek-v4.1-flash','deepseek-v4.1-flash-1017'))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ModelError('Direct DeepSeek redirect refused')


def direct_send(url: str,key: str,payload: dict[str,object],timeout: float) -> dict[str,object]:
    if url!=ENDPOINT+'/chat/completions':raise ModelError('Unapproved direct endpoint')
    request=Request(url,data=json.dumps(payload,ensure_ascii=False).encode(),method='POST',
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    opener=build_opener(ProxyHandler({}),NoRedirect,HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(request,timeout=timeout) as response:raw=response.read(4000001)
        if len(raw)>4000000:raise ModelError('Direct response exceeded size bound')
        value=json.loads(raw)
        if not isinstance(value,dict):raise ModelError('Invalid direct response object')
        return value
    except HTTPError as error:
        raise ModelError('Direct DeepSeek HTTP failure',diagnostics={'http_status':error.code}) from None
    except ModelError:raise
    except (OSError,ValueError):raise ModelError('Direct DeepSeek connection or response failure') from None


def load_direct_config(path: Path) -> ModelConfig:
    try:
        values=tomllib.loads(path.read_text(encoding='utf-8-sig'))['coder']
        key=values['api_key']
        if (values['provider']!='deepseek' or values['model']!='deepseek-flash' or values['effort']!='low'
            or values['base_url'].rstrip('/')!=ENDPOINT or not isinstance(key,str) or not key.strip()
            or key.strip() in ('SET_LOCALLY','<your-deepseek-key>')):raise ValueError
        return ModelConfig('coder','deepseek','deepseek-flash',key.strip(),ENDPOINT,'low','provider',
            max_output_tokens=values.get('max_output_tokens',65536))
    except (OSError,ValueError,KeyError,TypeError):
        raise ModelError('Configure the direct DeepSeek [coder] key and low policy in ignored ai.local.toml') from None


class DirectDeepSeekClient(ModelClient):
    def __init__(self,key: str,*,transport: Transport=direct_send,endpoint: str=ENDPOINT,
                 timeout: float=180,state: Path | None=None,purpose: str='coder',cap: int=65536) -> None:
        if endpoint.rstrip('/')!=ENDPOINT or not key.strip():raise ModelError('Direct key and approved endpoint required')
        if purpose not in ('coder','context_optimizer'):raise ValueError('Unsupported direct purpose')
        super().__init__(ModelConfig('coder','deepseek','deepseek-flash',key,ENDPOINT,'low','provider',
            max_output_tokens=cap),transport=transport,timeout=timeout)
        self.state,self.purpose=state,purpose
        self.last_usage: dict[str,int]={}

    def request_identity(self) -> dict[str,object]:
        return {'worker_backend':'deepseek_direct','semantic_role':self.purpose,
            'thinking_policy':'enabled-low','accepted_models_sha256':sha256(json.dumps(sorted(ACCEPTED_MODELS)).encode()).hexdigest()}

    def generate(self,prompt: str,*,max_output_tokens: int) -> ModelReply:
        if not prompt.strip():raise ModelError('Nonempty direct input required')
        self.validate_output_limit(max_output_tokens)
        if max_output_tokens>393216:raise ModelError('Direct output exceeds verified provider capacity')
        payload={'model':'deepseek-flash','messages':[{'role':'user','content':prompt}],
            'stream':False,'thinking':{'type':'enabled'},'reasoning_effort':'low',
            'max_tokens':max_output_tokens,'response_format':{'type':'json_object'}}
        try:data=self.transport(ENDPOINT+'/chat/completions',self.config.api_key,payload,self.timeout)
        except ModelError:raise
        except Exception:raise ModelError('Direct submission failed; usage remains uncertain') from None
        usage=data.get('usage',{});counts=None
        if isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_tokens','completion_tokens')):
            counts=(usage['prompt_tokens'],usage['completion_tokens'])
        details={} if counts is None else dict(input_tokens=counts[0],output_tokens=counts[1])
        try:
            choice=data['choices'][0];text=choice['message']['content']
            if (counts is None or choice.get('finish_reason')!='stop' or data.get('model') not in ACCEPTED_MODELS
                or not isinstance(data.get('id'),str) or not data['id'] or not isinstance(text,str) or not text.strip()
                or not isinstance(json.loads(text),dict)):raise ValueError
        except (KeyError,IndexError,TypeError,ValueError):
            raise ModelError('Direct response lacks complete valid JSON, model identity or usage',diagnostics=details) from None
        self.last_usage={k:v for k,v in usage.items() if type(v) is int and v>=0 and k in
            ('prompt_tokens','completion_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens','total_tokens')}
        return ModelReply(text,*counts,data['id'],data['model'])

    def generate_operation(self,operation_id: str,prompt: str,*,max_output_tokens: int) -> ModelReply:
        reply=self.generate(prompt,max_output_tokens=max_output_tokens)
        if self.state is not None:
            atomic_write(self.state,'direct-usage/'+sha256(operation_id.encode()).hexdigest()+'.json',json.dumps({
                'operation_id':operation_id,'purpose':self.purpose,'requested_model':self.config.model,
                'returned_model':reply.model,'effort':'low','usage':self.last_usage},sort_keys=True).encode())
        return reply
