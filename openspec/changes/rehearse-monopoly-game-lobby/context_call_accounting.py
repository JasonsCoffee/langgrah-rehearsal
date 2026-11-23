"""Durable selector identity/caching outside imported source and game units."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
from evidence_packet import Packet,canonical,assert_packet
from unity_coder.core.ai_models import ModelError
from unity_coder.core.storage import atomic_write,file_guard
if TYPE_CHECKING:
    from unity_coder.core.model_calls import ModelCalls


class CachedSelectionCalls:
    def __init__(self,calls: ModelCalls,state: Path,policy: str) -> None:
        self.calls,self.state,self.policy=calls,state,policy
        self.last_accounting={'actual_tokens':[0,0],'cache_hit':False,'original_tokens':None}

    def select(self,packet: Packet,unit: str,prompt: str) -> dict:
        assert_packet(packet)
        identity={'canonical':packet.canonical_sha256,'policy':self.policy,'unit':unit,
            'prompt_sha256':sha256(prompt.encode()).hexdigest()}
        key=sha256(canonical(identity).encode()).hexdigest();prefix='context-selection/'+key
        with file_guard(self.state,prefix+'.guard'):
            path=self.state/(prefix+'.json')
            if path.exists():
                value=json.loads(path.read_bytes())
                if value['identity']!=identity:raise ModelError('Cached selection identity changed')
                if 'result' not in value:raise ModelError('Prior selector submission requires reconciliation; no replay')
                self.last_accounting={'actual_tokens':[0,0],'cache_hit':True,'original_tokens':value['actual_usage'],
                    'call_id':'context-select-'+key}
                return value['result']
            atomic_write(self.state,prefix+'.json',canonical({'identity':identity,'state':'intent'}).encode())
            try:reply=self.calls.generate('context-select-'+key,unit,prompt,max_output_tokens=8192)
            except ModelError as error:
                detail=error.diagnostics
                if not all(type(detail.get(k)) is int and detail[k]>=0 for k in ('input_tokens','output_tokens')):raise
                # Native ModelCalls has already settled this rejected response.
                # Cache rejection, never replay it, and permit exact original fallback.
                result={'invalid_response':True}
                self.last_accounting={'actual_tokens':[detail['input_tokens'],detail['output_tokens']],
                    'cache_hit':False,'original_tokens':None,'call_id':'context-select-'+key,'failure_usage_known':True}
                atomic_write(self.state,prefix+'.json',canonical({'identity':identity,'result':result,
                    'state':'complete','actual_usage':[detail['input_tokens'],detail['output_tokens']],
                    'failure_usage_known':True}).encode())
                return result
            try:
                result=json.loads(reply.text)
                if not isinstance(result,dict):raise ValueError
            except ValueError:
                result={'invalid_response':True}
            atomic_write(self.state,prefix+'.json',canonical({'identity':identity,'result':result,
                'state':'complete','actual_usage':[reply.input_tokens,reply.output_tokens]}).encode())
            self.last_accounting={'actual_tokens':[reply.input_tokens,reply.output_tokens],'cache_hit':False,
                'original_tokens':None,'call_id':'context-select-'+key}
            return result


class PilotEnvelope:
    """An additional bound inside the existing ledger, never extra budget."""
    def __init__(self,ledger,state: Path,input_limit: int=10000000,output_limit: int=512000) -> None:
        self.ledger,self.state=ledger,state
        path=state/'context-optimization/pilot-envelope.json'
        if not path.exists():atomic_write(state,'context-optimization/pilot-envelope.json',canonical({
            'existing_calls':sorted(ledger._read()['calls']),'limits':[input_limit,output_limit]}).encode())
        self.before=json.loads(path.read_bytes())

    def check(self,input_reservation: int,output_reservation: int) -> None:
        calls=self.ledger._read()['calls'];used=[0,0]
        for call,value in calls.items():
            if call not in self.before['existing_calls']:
                for i,n in enumerate(value.get('actual',value['reserved'])):used[i]+=n
        if any(used[i]+n>self.before['limits'][i] for i,n in enumerate((input_reservation,output_reservation))):
            raise ModelError('Persistent pilot envelope cannot fit the next complete request')
