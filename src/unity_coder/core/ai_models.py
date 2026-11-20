"""Secret-safe local model configuration and blocking provider transport."""
from collections.abc import Callable
from dataclasses import dataclass, field
import json
import re
from pathlib import Path
import tomllib
from typing import Literal
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener


class ModelError(ValueError):
    """Sanitized operational error; never a unit defect."""
    def __init__(self, message: str, *, diagnostics: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class ModelConfig:
    role: Literal['coder', 'judge']
    provider: str
    model: str
    api_key: str = field(repr=False)
    base_url: str = 'https://openrouter.ai/api/v1'
    effort: str = ''
    temperature_mode: str = 'zero'
    upstream_provider: str = ''
    max_output_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.max_output_tokens is not None and (type(self.max_output_tokens) is not int or self.max_output_tokens < 1):
            raise ModelError('Configured model output cap must be a positive integer')


@dataclass(frozen=True)
class AIConfig:
    coder: ModelConfig
    judge: ModelConfig


@dataclass(frozen=True)
class ModelReply:
    text: str
    input_tokens: int
    output_tokens: int
    response_id: str
    model: str


def load_ai_config(path: Path) -> AIConfig:
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        raise ModelError('Cannot read valid local AI configuration') from None
    if set(data) != {'coder', 'judge'}:
        raise ModelError('AI configuration requires coder and judge sections')
    configs = []
    for role in ('coder', 'judge'):
        values = data[role]
        if not isinstance(values, dict) or set(values) - {'effort', 'temperature_mode', 'upstream_provider', 'max_output_tokens'} != {'provider','model','api_key','base_url'}:
            raise ModelError('Model configuration fields are missing or unsupported')
        if any(not isinstance(values[k], str) or not values[k].strip() for k in ('provider','model','api_key')):
            raise ModelError('Provider, model and API key must be populated')
        if not isinstance(values['base_url'], str):
            raise ModelError('Invalid model endpoint')
        provider = values['provider'].strip().casefold()
        if provider != 'openrouter':
            raise ModelError('Only the OpenRouter protocol is implemented')
        endpoint = values['base_url'].strip().rstrip('/') or 'https://openrouter.ai/api/v1'
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == 'https' and parsed.hostname and not parsed.username
                     and not parsed.password and not parsed.query and not parsed.fragment)
        except ValueError:
            valid = False
        if not valid:
            raise ModelError('Model endpoint must be HTTPS without credentials, query or fragment')
        effort = values.get('effort', '')
        if effort not in ('', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'):
            raise ModelError('Unsupported reasoning effort')
        temperature_mode = values.get('temperature_mode', 'zero')
        if temperature_mode not in ('zero', 'provider'):
            raise ModelError('Unsupported temperature policy')
        upstream = values.get('upstream_provider', '')
        if not isinstance(upstream,str) or (upstream and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]{0,99}',upstream)):
            raise ModelError('Invalid explicit upstream provider slug')
        configs.append(ModelConfig(role, provider, values['model'].strip(), values['api_key'].strip(), endpoint, effort, temperature_mode, upstream, values.get('max_output_tokens')))
    if configs[0].model.casefold() == configs[1].model.casefold():
        raise ModelError('Coder and judge require different model identities')
    return AIConfig(*configs)


Transport = Callable[[str, str, dict[str, object], float], dict[str, object]]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ModelError('Model endpoint redirect refused')


def send_chat(url: str, key: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
    request = Request(url, data=json.dumps(payload).encode(), method='POST',
                      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ModelError('Model response exceeds size limit')
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ModelError('Invalid model response object')
            return data
    except HTTPError as error:
        details: dict[str,object] = {'http_status':error.code}
        retry = error.headers.get('Retry-After','') if error.headers else ''
        if retry.isdigit():
            details['retry_after_seconds'] = min(int(retry),86400)
        try:
            metadata = json.loads(error.read(16384)).get('error',{}).get('metadata',{})
            for field_name in ('provider_name','limit_source'):
                value = metadata.get(field_name)
                if isinstance(value,str) and key not in value and re.fullmatch(r'[A-Za-z0-9_ ./-]{1,100}',value):
                    details[field_name] = value
        except (ValueError,AttributeError,TypeError,OSError):
            pass
        raise ModelError(f'Model provider HTTP {error.code}',diagnostics=details) from None
    except ModelError:
        raise
    except (OSError, ValueError):
        raise ModelError('Model connection or response failed') from None


class ModelClient:
    def __init__(self, config: ModelConfig, *, transport: Transport = send_chat, timeout: float = 60) -> None:
        if not 0 < timeout <= 180:
            raise ValueError('Model timeout must be bounded to 180 seconds')
        self.config, self.transport, self.timeout = config, transport, timeout

    def request_identity(self) -> dict[str, object]:
        """Backend-specific identity; legacy HTTP receipts remain unchanged."""
        return {}

    def reserve_input(self, prompt: str) -> int:
        """Conservative native framing allowance, overridable by agent harnesses."""
        return len(prompt.encode('utf-8')) + 1024

    def generate_operation(self, operation_id: str, prompt: str, *, max_output_tokens: int) -> ModelReply:
        """Keep durable operation identity available to non-HTTP worker backends."""
        return self.generate(prompt, max_output_tokens=max_output_tokens)

    def validate_output_limit(self, max_output_tokens: int) -> None:
        """Validate before durable reservation as well as direct transport calls."""
        if type(max_output_tokens) is not int or max_output_tokens < 1:
            raise ModelError('Positive integer output allowance required')
        cap = self.config.max_output_tokens
        if cap is not None and max_output_tokens > cap:
            raise ModelError('Requested allowance exceeds configured model output cap')

    def generate(self, prompt: str, *, max_output_tokens: int) -> ModelReply:
        if not prompt.strip():
            raise ModelError('Nonempty prompt required')
        self.validate_output_limit(max_output_tokens)
        payload: dict[str, object] = dict(model=self.config.model, stream=False,
            messages=[{'role':'user','content':prompt}], max_completion_tokens=max_output_tokens,
            temperature=0, provider={'require_parameters':True, 'allow_fallbacks':False})
        if self.config.effort:
            payload['reasoning'] = {'effort': self.config.effort}
        if self.config.temperature_mode == 'provider':
            payload.pop('temperature')
        if self.config.upstream_provider:
            payload['provider']['only'] = [self.config.upstream_provider]
        try:
            data = self.transport(self.config.base_url + '/chat/completions', self.config.api_key, payload, self.timeout)
        except ModelError:
            raise
        except Exception:
            # A timed-out request may have been billed. Never automatically replay.
            raise ModelError('Model transport failed; usage remains uncertain') from None
        try:
            if 'error' in data:
                raise ValueError
            choice = data['choices'][0]
            text = choice['message']['content']
            usage = data['usage']
            counts = (usage['prompt_tokens'], usage['completion_tokens'])
            if (choice.get('finish_reason') != 'stop' or not isinstance(text,str) or not text.strip()
                or any(type(n) is not int or n < 0 for n in counts)
                or not isinstance(data.get('id'),str) or not isinstance(data.get('model'),str)):
                raise ValueError
            return ModelReply(text, *counts, data['id'], data['model'])
        except (KeyError, IndexError, TypeError, ValueError):
            details: dict[str,object] = {}
            usage = data.get('usage',{})
            if isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_tokens','completion_tokens')):
                details.update(input_tokens=usage['prompt_tokens'],output_tokens=usage['completion_tokens'])
            choices = data.get('choices')
            if isinstance(choices,list) and choices and isinstance(choices[0],dict):
                choice = choices[0]
                finish = choice.get('finish_reason')
                if finish in ('stop','length','error','content_filter','tool_calls',None):
                    details['finish_reason'] = finish
                message = choice.get('message')
                if isinstance(message,dict) and isinstance(message.get('content'),str):
                    details['partial_content'] = message['content'][:4_000_000].replace(self.config.api_key,'[redacted]')
            raise ModelError('Model response missing complete content or valid usage',diagnostics=details) from None
