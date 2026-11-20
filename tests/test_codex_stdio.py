"""Frozen protocol/isolation checks; fake RPC never starts a real agent."""
from pathlib import Path
import pytest
from test_codex_backend import turn_events
from unity_coder.core.ai_models import ModelError


class Rpc:
    def __init__(self,request, *, bad=None):self.calls=[];self.request=request;self.bad=bad;self.closed=False
    def call(self,method,params):
        self.calls.append((method,params))
        if method=='initialize':return {'userAgent':'Codex/test'}
        if method=='model/list':return {'data':[{'model':'model-coder','supportedReasoningEfforts':[{'reasoningEffort':'low'}]}]}
        if method=='thread/start':return {'thread':{'id':'thread'},'model':'other' if self.bad=='model' else 'model-coder',
            'modelProvider':'openai','sandbox':{'type':'workspaceWrite' if self.bad=='sandbox' else 'readOnly'},
            'approvalPolicy':'never','cwd':self.request['cwd']}
        if method=='turn/start':return {'turn':{'id':'turn'}}
        raise AssertionError(method)
    def notify(self,method,params=None):self.calls.append((method,params))
    def events(self):return iter(turn_events())
    def close(self):self.closed=True


def request(tmp_path):
    return {'operation_id':'operation','model':'model-coder','role':'coder','effort':'low','cwd':str(tmp_path),
        'prompt':'approved source contract','timeout':60,'sandbox':'read-only','tools_enabled':False,
        'fresh_context':True,'budget_enforcement':'dispatch_accounting','input_allocation':20000,'output_allocation':64}


def test_transport_starts_only_fresh_readonly_explicit_model_session(tmp_path):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    req=request(tmp_path);rpc=Rpc(req)
    exchange=CodexStdioExchange(rpc_factory=lambda cmd,timeout:rpc,disabled_mcp=('existing_server',))
    events=list(exchange(req))
    assert events==turn_events() and rpc.closed
    start=next(params for method,params in rpc.calls if method=='thread/start')
    assert start['model']=='model-coder' and start['modelProvider']=='openai'
    assert start['allowProviderModelFallback'] is False and start['ephemeral'] is True
    assert start['sandbox']=='read-only' and start['approvalPolicy']=='never'
    assert not any(method in ('thread/resume','thread/fork') for method,_ in rpc.calls)
    turn=next(params for method,params in rpc.calls if method=='turn/start')
    assert turn['input']==[{'type':'text','text':'approved source contract'}]
    assert 'max_output_tokens' not in turn and 'max_completion_tokens' not in turn


@pytest.mark.parametrize('bad',['model','sandbox'])
def test_effective_model_and_sandbox_are_verified_before_inference(tmp_path,bad):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    req=request(tmp_path);rpc=Rpc(req,bad=bad)
    exchange=CodexStdioExchange(rpc_factory=lambda cmd,timeout:rpc)
    with pytest.raises(ModelError):list(exchange(req))
    assert not any(method=='turn/start' for method,_ in rpc.calls) and rpc.closed


def test_command_disables_existing_tools_without_sending_credentials(tmp_path):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    req=request(tmp_path);rpc=Rpc(req);seen=[]
    def factory(command,timeout):seen.append(command);return rpc
    list(CodexStdioExchange(rpc_factory=factory,disabled_mcp=('existing_server',))(req))
    args=seen[0]
    for item in ['features.shell_tool=false','features.apps=false','features.plugins=false',
        'features.memories=false','agents.enabled=false','web_search="disabled"',
        'mcp_servers.existing_server.enabled=false']:
        assert item in args
    assert all('api_key' not in item and 'Bearer' not in item for item in args)


@pytest.mark.parametrize('change',['tools','history','mode','timeout'])
def test_unsafe_requests_fail_before_starting_rpc(tmp_path,change):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    req=request(tmp_path)
    if change=='tools':req['tools_enabled']=True
    elif change=='history':req['fresh_context']=False
    elif change=='mode':req['budget_enforcement']='require_hard_caps'
    else:req['timeout']=1000
    def fail(*args):pytest.fail('must not start RPC')
    with pytest.raises(ModelError):list(CodexStdioExchange(rpc_factory=fail)(req))


@pytest.mark.parametrize('name',['server.with.dot','server with space'])
def test_unsupported_mcp_override_keys_fail_closed(tmp_path,name):
    from unity_coder.core.codex_stdio import CodexStdioExchange
    def fail(*args):pytest.fail('must not start a server with ambiguous MCP keys')
    with pytest.raises(ModelError,match='MCP'):
        list(CodexStdioExchange(rpc_factory=fail,disabled_mcp=(name,))(request(tmp_path)))
