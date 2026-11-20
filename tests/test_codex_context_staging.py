"""Frozen checks: oversized context is staged without losing evidence or usage."""
import json
import pytest
from test_codex_stdio import Rpc,request
from test_codex_backend import turn_events
from unity_coder.core.ai_models import ModelError


def test_staging_exact_context_and_cumulative_usage(tmp_path):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    from unity_coder.core.codex_backend import parse_turn_events
    req=request(tmp_path);req['prompt']='x'*1049000
    class StagedRpc(Rpc):
        def events(self):
            turns=[p for m,p in self.calls if m=='turn/start'];n=len(turns)
            events=turn_events()
            for event in events:
                p=event['params']
                if p.get('turnId'):p['turnId']='turn'+str(n)
                if event['method']=='item/completed' and p['item']['type']=='agentMessage':
                    p['item']['text']='CONTEXT RECEIVED' if n==1 else '{"files":{}}'
                if event['method']=='thread/tokenUsage/updated':
                    u=p['tokenUsage']['total'];u.update(inputTokens=100*n,outputTokens=10*n,totalTokens=110*n,cachedInputTokens=0,reasoningOutputTokens=0)
                if event['method']=='turn/completed':p['turn']['id']='turn'+str(n)
            return iter(events)
        def call(self,method,params):
            answer=super().call(method,params)
            if method=='turn/start':answer['turn']['id']='turn'+str(sum(m=='turn/start' for m,p in self.calls))
            return answer
    rpc=StagedRpc(req)
    result=parse_turn_events(CodexStdioExchange(rpc_factory=lambda c,t:rpc)(req))
    turns=[p for m,p in rpc.calls if m=='turn/start']
    assert len(turns)==2 and all(len(p['input'][0]['text'])<=1048576 for p in turns)
    assert ''.join(p['input'][0]['text'].split('\nCONTEXT PART\n',1)[1] for p in turns)==req['prompt']
    assert result.input_tokens==200 and result.output_tokens==20
    assert len(result.context_turns)==1 and result.context_turns[0]['input_tokens']==100
    assert rpc.closed


def test_context_acknowledgement_cannot_admit_early_patch(tmp_path):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    req=request(tmp_path);req['prompt']='x'*1049000;rpc=Rpc(req)
    with pytest.raises(ModelError):list(CodexStdioExchange(rpc_factory=lambda c,t:rpc)(req))
    assert len([1 for m,p in rpc.calls if m=='turn/start'])==1 and rpc.closed


def test_sanitized_rpc_error_keeps_code_without_raw_message():
    from unity_coder.core.codex_stdio import StdioRpc
    rpc=object.__new__(StdioRpc);rpc.sequence=0;rpc.pending=[];rpc._send=lambda value:None
    rpc._next=lambda:{'id':1,'error':{'code':-32602,'message':'secret provider payload'}}
    with pytest.raises(ModelError) as caught:rpc.call('turn/start',{})
    assert caught.value.diagnostics['rpc_code']==-32602
    assert 'secret' not in json.dumps(caught.value.diagnostics)
