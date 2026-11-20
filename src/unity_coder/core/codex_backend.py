"""Opt-in Codex sessions with native receipts and explicit budget semantics."""
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from .ai_models import ModelClient, ModelConfig, ModelError, ModelReply
from .ownership import portable_path
from .storage import atomic_write, file_guard


@dataclass(frozen=True)
class CodexPolicy:
    role: Literal['coder', 'judge']
    model: str
    effort: str
    budget_mode: Literal['require_hard_caps', 'dispatch_accounting'] = 'require_hard_caps'
    authorization_ref: str = ''
    max_calls: int = 1
    framing_tokens: int = 16384

    def __post_init__(self) -> None:
        if (self.role not in ('coder','judge') or not self.model.strip()
            or self.effort not in ('low','medium','high','xhigh','max')
            or self.budget_mode not in ('require_hard_caps','dispatch_accounting')
            or type(self.max_calls) is not int or self.max_calls < 1
            or type(self.framing_tokens) is not int or self.framing_tokens < 16384):
            raise ValueError('Invalid explicit Codex worker policy')
        if self.authorization_ref:
            portable_path(self.authorization_ref)
        elif self.budget_mode == 'dispatch_accounting':
            raise ValueError('Dispatch accounting requires authorization provenance')

    @property
    def sha256(self) -> str:
        return sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class CodexTurnResult:
    text: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    reasoning_output_tokens: int
    thread_id: str
    turn_id: str


def parse_turn_events(events: Iterable[dict]) -> CodexTurnResult:
    """Require one completed agent answer with attributable aggregate usage."""
    thread = turn = ''
    answer: str | None = None
    usage: dict | None = None
    completed = False
    for event in events:
        method = event.get('method','')
        params = event.get('params',{})
        if method == 'model/rerouted':
            raise ModelError('Codex model rerouting is forbidden')
        event_thread = params.get('threadId')
        event_turn = params.get('turnId')
        if event_thread:
            if thread and thread != event_thread:raise ModelError('Codex thread identity changed')
            thread = event_thread
        if event_turn:
            if turn and turn != event_turn:raise ModelError('Codex turn identity changed')
            turn = event_turn
        if method in ('item/started','item/completed'):
            item = params.get('item',{})
            if item.get('type') not in ('agentMessage','reasoning','userMessage'):
                raise ModelError('Unexpected Codex tool activity; no result admitted')
            if (method == 'item/completed' and item.get('type') == 'agentMessage'
                and item.get('phase') in (None,'final_answer')):
                if answer is not None or not isinstance(item.get('text'),str):
                    raise ModelError('Ambiguous Codex final answer')
                answer = item['text']
        if method == 'thread/tokenUsage/updated':
            current = params.get('tokenUsage',{}).get('total')
            keys = ('inputTokens','outputTokens','cachedInputTokens','reasoningOutputTokens','totalTokens')
            if not isinstance(current,dict) or any(type(current.get(k)) is not int or current[k]<0 for k in keys):
                raise ModelError('Invalid Codex usage receipt')
            if (current['totalTokens'] != current['inputTokens']+current['outputTokens']
                or current['cachedInputTokens']>current['inputTokens']
                or current['reasoningOutputTokens']>current['outputTokens']):
                raise ModelError('Inconsistent Codex usage receipt')
            if usage and any(current[k]<usage[k] for k in keys):
                raise ModelError('Codex cumulative usage decreased')
            usage = current
        if method == 'turn/completed':
            detail = params.get('turn',{})
            if completed or detail.get('status') != 'completed' or (turn and detail.get('id')!=turn):
                raise ModelError('Codex turn did not complete unambiguously')
            turn = detail.get('id','')
            completed = True
    if not completed or usage is None or not thread or not turn or not answer:
        raise ModelError('Completed Codex answer and usage receipt required')
    return CodexTurnResult(answer,usage['inputTokens'],usage['outputTokens'],
        usage['cachedInputTokens'],usage['reasoningOutputTokens'],thread,turn)


class CodexModelClient(ModelClient):
    """Native paid-call client; authorization comes only from trusted host code."""
    def __init__(self, policy: CodexPolicy, state: Path, working_root: Path, *,
                 exchange: Callable[[dict], Iterable[dict]],
                 authorize: Callable[[str], bool], timeout: float = 60,
                 session_timeout: float | None = None) -> None:
        super().__init__(ModelConfig(policy.role,'codex',policy.model,'',
            base_url='stdio://codex-app-server',effort=policy.effort,temperature_mode='provider'),timeout=timeout)
        session_timeout=timeout if session_timeout is None else session_timeout
        if type(session_timeout) not in (int,float) or not 0<session_timeout<=600:
            raise ValueError('Codex session deadline must be bounded to 600 seconds')
        self.session_timeout=session_timeout
        self.policy,self.state,self.working_root = policy,state,working_root.resolve(strict=True)
        if self.state.resolve().is_relative_to(self.working_root):
            raise ValueError('Codex worker root must exclude trusted receipt state')
        self.exchange,self.authorize = exchange,authorize

    def validate_output_limit(self, max_output_tokens: int) -> None:
        super().validate_output_limit(max_output_tokens)
        if self.policy.budget_mode == 'require_hard_caps':
            raise ModelError('Installed Codex protocol has no verified hard input/output caps; no dispatch')
        if not self.authorize(self.policy.sha256):
            raise ModelError('Explicit Codex dispatch-accounting authorization required')

    def request_identity(self) -> dict[str, object]:
        return {'worker_backend':'codex_app_server','backend_policy_sha256':self.policy.sha256,
                'budget_enforcement':self.policy.budget_mode}

    def reserve_input(self, prompt: str) -> int:
        return len(prompt.encode('utf-8'))+self.policy.framing_tokens

    def generate(self, prompt: str, *, max_output_tokens: int) -> ModelReply:
        raise ModelError('Codex requires a durable generate_operation call identity')

    def generate_operation(self, operation_id: str, prompt: str, *, max_output_tokens: int) -> ModelReply:
        self.validate_output_limit(max_output_tokens)
        key = sha256(operation_id.encode()).hexdigest()
        prefix = 'codex-claims/'+self.policy.sha256
        with file_guard(self.state,prefix+'/claims.guard'):
            folder = self.state/prefix
            if (folder/(key+'.json')).exists():
                raise ModelError('Existing Codex claim requires owner reconciliation; no replay')
            if len(tuple(folder.glob('*.json'))) >= self.policy.max_calls:
                raise ModelError('Authorized Codex claim limit reached',diagnostics={'input_tokens':0,'output_tokens':0})
            atomic_write(self.state,prefix+'/'+key+'.json',json.dumps({
                'operation_id':operation_id,'policy_sha256':self.policy.sha256,
                'prompt_sha256':sha256(prompt.encode()).hexdigest()}).encode())
        request = {'operation_id':operation_id,'role':self.policy.role,'model':self.policy.model,
            'effort':self.policy.effort,'prompt':prompt,'cwd':str(self.working_root),
            'input_allocation':self.reserve_input(prompt),'output_allocation':max_output_tokens,
            'budget_enforcement':self.policy.budget_mode,'timeout':self.session_timeout,
            'sandbox':'read-only','tools_enabled':False,'fresh_context':True}
        events = None
        try:
            events = iter(self.exchange(request))
            result = parse_turn_events(events)
        except ModelError:
            raise
        except Exception:
            raise ModelError('Codex exchange requires owner reconciliation; no automatic replay') from None
        finally:
            close = getattr(events,'close',None)
            if callable(close):close()
        receipt = {'operation_id':operation_id,'policy_sha256':self.policy.sha256,
            'prompt_sha256':sha256(prompt.encode()).hexdigest(),**asdict(result)}
        atomic_write(self.state,'codex-receipts/'+key+'.json',json.dumps(receipt,sort_keys=True).encode())
        if result.input_tokens>request['input_allocation'] or result.output_tokens>max_output_tokens:
            raise ModelError('Codex actual usage exceeded dispatch allocation',diagnostics={
                'input_tokens':result.input_tokens,'output_tokens':result.output_tokens})
        return ModelReply(result.text,result.input_tokens,result.output_tokens,
                          result.thread_id+'/'+result.turn_id,self.policy.model)
