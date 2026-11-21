"""Rehearsal boundary diagnostics without changing native dispatch or validation."""
from __future__ import annotations
from hashlib import sha256
import json
from typing import TYPE_CHECKING
from unity_coder.core.ai_models import ModelError
from unity_coder.core.storage import atomic_write
if TYPE_CHECKING:
    from unity_coder.core.model_calls import ModelCalls
    from unity_coder.core.ai_models import ModelReply

MESSAGES={
    'Codex RPC stream ended unexpectedly':'stream_ended',
    'Codex RPC deadline exceeded':'deadline',
    'Codex turn did not complete unambiguously':'incomplete_turn',
    'Completed Codex answer and usage receipt required':'missing_completed_receipt',
    'Ambiguous Codex final answer':'ambiguous_answer',
    'Codex model rerouting is forbidden':'reroute_rejected',
    'Codex thread identity changed':'identity_changed',
    'Codex turn identity changed':'identity_changed',
    'Unexpected Codex worker thread':'identity_changed',
    'Unexpected Codex worker turn':'identity_changed',
    'Codex cumulative usage decreased':'usage_decreased',
    'Invalid Codex usage receipt':'invalid_usage',
    'Inconsistent Codex usage receipt':'inconsistent_usage',
    'Unexpected Codex tool or approval request':'disallowed_tool_request',
    'Codex context staging did not acknowledge the exact partial context':'invalid_context_ack',
    'Context staging acknowledgement required':'invalid_context_ack',
    'Existing Codex claim requires owner reconciliation; no replay':'existing_claim',
    'Codex effective model or sandbox differs from requested policy':'policy_mismatch',
    'Requested Codex model/effort is not available; no fallback':'model_unavailable',
}


def generate(calls: ModelCalls,call: str,unit: str,prompt: str,output_tokens: int) -> ModelReply:
    try:return calls.generate(call,unit,prompt,max_output_tokens=output_tokens)
    except ModelError as error:
        config=calls.client.config
        if config.provider=='codex':
            message=str(error);code=MESSAGES.get(message,'unclassified_codex_error')
            if message in {'Codex RPC rejected '+method for method in ('initialize','model/list','thread/start','turn/start')}:
                code='rpc_rejected'
            data={'call_id':call,'unit':unit,'role':config.role,'model':config.model,'effort':config.effort,
                'message_code':code,'message_sha256':sha256(message.encode()).hexdigest(),
                'message_characters':len(message),'diagnostic_keys':sorted(set(error.diagnostics)&{
                    'input_tokens','output_tokens','transport','protocol_phase','item_type','event_method',
                    'rpc_method','rpc_code','failure_kind','exception_type'}),
                'prompt_sha256':sha256(prompt.encode()).hexdigest(),'original_error_reraised':True}
            atomic_write(calls.budget.root,'diagnostics/codex-errors/'+sha256(call.encode()).hexdigest()+'.json',
                json.dumps(data,sort_keys=True).encode())
        raise
