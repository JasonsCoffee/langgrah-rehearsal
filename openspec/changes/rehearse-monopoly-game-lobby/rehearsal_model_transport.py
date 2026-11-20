"""Rehearsal-only reasoning allocation and credential-free response diagnostics."""
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.ai_models import send_chat
from unity_coder.core.storage import atomic_write
from verified_openrouter import send_verified_openrouter
from schannel_openrouter import send_schannel_openrouter
from preconnected_openrouter import send_preconnected_openrouter

def component_label(role: str, model: str, effort: str) -> str:
    names={'deepseek/deepseek-v4.1-flash':'DS4.1 Flash','openai/gpt-6.1-sol':'GPT-6.1 Sol'}
    return ('Judge' if role=='judge' else 'Coder')+' ('+names.get(model,model)+', '+(effort or 'provider default')+')'

class RehearsalTransport:
    def __init__(self,state: Path,role: str):
        self.state,self.role=state,role

    def __call__(self,url,key,payload,timeout):
        request=dict(payload)
        direct_policy=self.state/('network-policy.sol-preconnect.json' if self.role=='judge' else 'network-policy.coder-preconnect.json')
        preconnect=((self.role=='judge' and request.get('model')=='openai/gpt-6.1-sol')
            or (self.role=='coder' and request.get('model')=='deepseek/deepseek-v4.1-flash')) and direct_policy.exists()
        if preconnect and json.loads(direct_policy.read_bytes())!={
            'format_version':1,'profile':'verified_direct_preconnect','automatic_retries':0,
            'certificate_verification':'required','tls_establishment_attempts':3}:
            raise ValueError('Unrecognized direct TLS establishment policy')
        sol_policy=self.state/'network-policy.sol-schannel.json'
        schannel=self.role=='judge' and request.get('model')=='openai/gpt-6.1-sol' and sol_policy.exists()
        if schannel and json.loads(sol_policy.read_bytes())!={
            'format_version':1,'profile':'verified_schannel_curl','automatic_retries':0,
            'certificate_verification':'required','revocation':'best_effort'}:
            raise ValueError('Unrecognized trusted Sol network policy')
        network_policy=self.state/'network-policy.openrouter.json'
        tls_compat=network_policy.exists()
        if tls_compat and json.loads(network_policy.read_bytes())!={
            'format_version':1,'profile':'verified_tls12_app_identity','automatic_retries':0,'certificate_verification':'required'}:
            raise ValueError('Unrecognized trusted OpenRouter network policy')
        # The explicitly selected GLM judge otherwise wraps valid JSON in fences.
        # Request wire-level JSON; keep native schema validation and raw receipts.
        if self.role=='judge' and request.get('model') in ('z-ai/glm-5.3-flash','openai/gpt-6.1-sol'):
            request.setdefault('response_format',{'type':'json_object'})
        try:
            task_body=request['messages'][0]['content'].partition('\n')[2].split('\nFINAL TASK INSTRUCTIONS:\n',1)[0]
            task_stage=json.loads(task_body).get('stage')
        except (ValueError,KeyError,TypeError,IndexError,AttributeError):task_stage=None
        if (self.role=='coder' and request.get('model')=='deepseek/deepseek-v4.1-flash'
            and task_stage in ('test_authoring','green','refactor')):
            request.setdefault('response_format',{'type':'json_object'})
        # Live evidence showed Alibaba ignored reasoning.max_tokens and used
        # every completion token for reasoning. The same advertised model has
        # optional reasoning and explicitly supports effort none. Only select
        # that mode when the role has no explicit configured effort override.
        serialization_policy=self.state/'author-serialization-policy.json'
        direct_author=False
        if self.role=='coder' and serialization_policy.exists():
            if (json.loads(serialization_policy.read_bytes())!={
                'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
                'non_harness_authoring_effort':'none','explicit_effort_precedence':True}
                or request.get('model')!='deepseek/deepseek-v4.1-flash'):
                raise ValueError('Unrecognized optional author serialization policy')
            direct_author=True
        unit_policy=self.state/'author-unit-effort-policy.json'
        scoped_author=False
        if self.role=='coder' and unit_policy.exists():
            if (json.loads(unit_policy.read_bytes())!={
                'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
                'stage':'test_authoring',
                'owned_csharp_path':'Tests/Runtime/Script/LobbyRehearsal/LobbyChatMessageTests.cs',
                'effort':'low','explicit_effort_precedence':True}
                or request.get('model')!='deepseek/deepseek-v4.1-flash'):
                raise ValueError('Unrecognized optional unit effort policy')
            scoped_author=True
        chat_policy=self.state/'author-chat-effort-policy.json'
        scoped_chat=False
        if self.role=='coder' and chat_policy.exists():
            if (json.loads(chat_policy.read_bytes())!={
                'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
                'stage':'test_authoring',
                'owned_csharp_path':'Tests/Runtime/Script/LobbyRehearsal/LobbySocialChatTests.cs',
                'effort':'low','explicit_effort_precedence':True}
                or request.get('model')!='deepseek/deepseek-v4.1-flash'):
                raise ValueError('Unrecognized optional chat effort policy')
            scoped_chat=True
        cards_policy=self.state/'author-cards-effort-policy.json'
        scoped_cards=False
        if self.role=='coder' and cards_policy.exists():
            if (json.loads(cards_policy.read_bytes())!={
                'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
                'stage':'test_authoring',
                'owned_csharp_path':'Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyRechargeTests.cs',
                'effort':'low','explicit_effort_precedence':True}
                or request.get('model')!='deepseek/deepseek-v4.1-flash'):
                raise ValueError('Unrecognized optional cards effort policy')
            scoped_cards=True
        records_policy=self.state/'author-records-effort-policy.json'
        scoped_records=False
        if self.role=='coder' and records_policy.exists():
            if (json.loads(records_policy.read_bytes())!={
                'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
                'stage':'test_authoring',
                'owned_csharp_path':'Tests/Runtime/Script/LobbyRehearsal/LobbyRecordsSettingsTests.cs',
                'effort':'low','explicit_effort_precedence':True}
                or request.get('model')!='deepseek/deepseek-v4.1-flash'):
                raise ValueError('Unrecognized optional records effort policy')
            scoped_records=True
        if self.role=='coder' and not request.get('reasoning'):
            try:
                body=request['messages'][0]['content'].partition('\n')[2].split('\nFINAL TASK INSTRUCTIONS:\n',1)[0]
                job=json.loads(body)
                harness=any(path.endswith('LobbyHarness.cs') for path in job.get('owns',[]))
                authoring=job.get('stage')=='test_authoring'
            except (ValueError,KeyError,TypeError):
                harness=False
                authoring=False
            # The shared harness benefited from low-effort planning. Consumer
            # file emission uses its already-reviewed scaffolding and the final
            # task/repair tail, reserving the full native allowance for code.
            request['reasoning']={'effort':'low' if harness or (authoring and not direct_author) else 'none'}
            if (scoped_author and authoring
                and 'Tests/Runtime/Script/LobbyRehearsal/LobbyChatMessageTests.cs' in job.get('owns',[])):
                request['reasoning']={'effort':'low'}
            if (scoped_chat and authoring
                and 'Tests/Runtime/Script/LobbyRehearsal/LobbySocialChatTests.cs' in job.get('owns',[])):
                request['reasoning']={'effort':'low'}
            if (scoped_cards and authoring
                and 'Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyRechargeTests.cs' in job.get('owns',[])):
                request['reasoning']={'effort':'low'}
            if (scoped_records and authoring
                and 'Tests/Runtime/Script/LobbyRehearsal/LobbyRecordsSettingsTests.cs' in job.get('owns',[])):
                request['reasoning']={'effort':'low'}
        encoded=json.dumps(request,sort_keys=True).encode()
        token=sha256(encoded).hexdigest()
        label=component_label(self.role,request['model'],request.get('reasoning',{}).get('effort',''))
        print(label,'request',flush=True)
        policy={'role':self.role,'component_label':label,'requested_model':request['model'],
            'provider':request['provider'],'temperature':request.get('temperature'),
            'reasoning_allocation':request.get('reasoning'),
            'response_format':request.get('response_format'),
            'tls_profile':'verified_direct_preconnect' if preconnect else ('verified_schannel_curl' if schannel else ('verified_tls12_app_identity' if tls_compat else 'native_default')),
            'completion_limit':request['max_completion_tokens'],'request_sha256':token}
        atomic_write(self.state,'provider-diagnostics/'+token+'.request.json',json.dumps(policy,indent=2).encode())
        result=(send_preconnected_openrouter if preconnect else (send_schannel_openrouter if schannel else (send_verified_openrouter if tls_compat else send_chat)))(url,key,request,timeout)
        choices=[]
        for choice in result.get('choices',[]):
            message=choice.get('message',{})
            content=message.get('content')
            reasoning=message.get('reasoning',message.get('reasoning_content'))
            choices.append({'finish_reason':choice.get('finish_reason'),
                'content_type':type(content).__name__,'content_characters':len(content) if isinstance(content,str) else 0,
                'reasoning_characters':len(reasoning) if isinstance(reasoning,str) else 0,
                'message_fields':sorted(message)})
        summary=policy|{'response_id':result.get('id'),'response_model':result.get('model'),
            'response_provider':result.get('provider'),'usage':result.get('usage'),'choices':choices}
        atomic_write(self.state,'provider-diagnostics/'+token+'.response.json',json.dumps(summary,indent=2).encode())
        return result
