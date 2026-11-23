"""Explicit mixed clients; historical grants and receipts remain immutable."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.ai_models import AIConfig,ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.codex_backend import CodexModelClient,CodexPolicy
from unity_coder.core.codex_stdio import CodexStdioExchange
from unity_coder.core.storage import atomic_write
from direct_deepseek_client import load_direct_config,DirectDeepSeekClient

QUALIFICATION_REF='context-optimization/pilot-packed-v2-qualified.json'


def backend_record() -> dict:
    return {'run_id':'monopoly-game-lobby','backend':'mixed','profile_sha256':profile_sha256(),
        'packing_format_version':2,'qualification_ref':QUALIFICATION_REF,
        'authorization_ref':role_profile()['authorization_ref'],'source_filter_version':2}


def selected_backend(state: Path,requested: str | None) -> str:
    path=state/'model-authorizations/active-backend.json'
    if path.exists():
        if json.loads(path.read_bytes())!=backend_record():raise ValueError('Active backend policy changed')
        if requested not in (None,'mixed'):raise ValueError('Stale backend override conflicts with the activated policy')
        return 'mixed'
    return requested or 'openrouter'


def activate_backend(state: Path,budget: BudgetLedger) -> None:
    qualification=active_qualification(state,budget._read()['calls'])
    path=state/'context-optimization/packed-v2-clean-compile-audit.json'
    audit=json.loads(path.read_bytes())
    operation='v70-migration-packed-v2-clean-compile-ECON'
    if (audit.get('audit_passed') is not True or audit.get('packing_format_version')!=2
        or audit.get('source_filter_version')!=2
        or budget.limits!=role_profile()['limits']):raise ValueError('Verified live audit and unchanged limits required')
    live=json.loads((state/'context-optimization/live-audit.json').read_bytes())
    row=next((r for r in live['reviews'] if r['operation']==operation),None)
    if not row or row.get('audit',{}).get('routing_agrees') is not True:
        raise ValueError('Genuine canonical comparison required before persistent activation')
    for call in (operation,operation+'-shadow-audit'):
        proof=qualification|{'roles':{'coder':qualification['roles']['coder'],'judge':call}}
        validate_pilot_receipts(state,budget._read()['calls'],proof)
    marker=state/'model-authorizations/active-backend.json'
    record=backend_record()
    if marker.exists():
        prior=marker.read_bytes();value=json.loads(prior)
        if value==record:return
        legacy={k:v for k,v in record.items() if k!='source_filter_version'}
        if value!=legacy:raise ValueError('Preserve different existing backend activation')
        history='model-authorizations/activation-history/'+sha256(prior).hexdigest()+'.json'
        if (state/history).exists() and (state/history).read_bytes()!=prior:raise ValueError('Activation history changed')
        if not (state/history).exists():atomic_write(state,history,prior)
        atomic_write(state,'model-authorizations/active-backend.json',json.dumps(record,sort_keys=True).encode())
    else:atomic_write(state,'model-authorizations/active-backend.json',json.dumps(record,sort_keys=True).encode())


def active_qualification(state: Path,calls: dict) -> dict:
    qualification=json.loads((state/QUALIFICATION_REF).read_bytes())
    if qualification.get('packing_format_version')!=2:
        raise ValueError('Current exact packing format requires its own genuine pilot')
    validate_pilot_receipts(state,calls,qualification)
    from packet_archive import read_packet
    from evidence_context_guard import private_note_ids
    for case in qualification.get('cases',[]):
        identity=case['canonical_sha256']
        packet=read_packet(state/'context-packets'/identity/'canonical.json',identity)
        if private_note_ids(packet):raise ValueError('Pilot contains inadmissible author reports')
    return qualification


def role_profile() -> dict:
    coder={'provider':'deepseek','model':'deepseek-flash','effort':'low'}
    return {'version':1,'coder':coder,'optimizer':dict(coder),
        'judge':{'provider':'codex','model':'gpt-6.1-sol','effort':'low'},
        'coder_stages':['test_authoring','green','refactor','format_repair'],
        'limits':[250000000,24000000,160,2],'authorization_ref':'model-authorizations/direct-deepseek-low.json',
        'selector_output':8192,'judge_output':32768,'coder_output':65536,
        'pilot_limits':[10000000,512000],'framing_tokens':65536,'max_calls_per_role':200}


def validate_judge_policy(effort: str,digest: str,grant: dict | None) -> None:
    if effort=='medium':return
    if effort!='low' or not grant or grant.get('judge_effort')!='low' or grant.get('judge_policy_sha256')!=digest:
        raise ValueError('Explicit matching low-effort Judge grant required')


def judge_policy() -> CodexPolicy:
    profile=role_profile()
    return CodexPolicy('judge','gpt-6.1-sol','low','dispatch_accounting',profile['authorization_ref'],
        profile['max_calls_per_role'],profile['framing_tokens'])


def profile_sha256() -> str:
    return sha256(json.dumps(role_profile(),sort_keys=True).encode()).hexdigest()


def validate_pilot_receipts(state: Path,calls: dict,qualification: dict) -> None:
    try:
        if (qualification.get('profile_sha256')!=profile_sha256() or qualification.get('roles_qualified') is not True
            or qualification.get('comparison_passed') is not True or set(qualification['roles'])!={'coder','judge'}):raise ValueError
        for role in ('coder','judge'):
            call=qualification['roles'][role];key=sha256(call.encode()).hexdigest()
            record=json.loads((state/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json')).read_bytes())
            identity,reply=record['identity'],record['reply'];policy=role_profile()[role]
            if (identity['call_id']!=call or identity['role']!=role or identity['effort']!='low'
                or identity['model']!=policy['model'] or identity['provider']!=policy['provider']
                or calls[call].get('actual')!=[reply['input_tokens'],reply['output_tokens']]
                or any(type(reply[k]) is not int or reply[k]<=0 for k in ('input_tokens','output_tokens'))):raise ValueError
            if role=='judge':
                sdk=json.loads((state/'codex-receipts'/(key+'.json')).read_bytes())
                if (identity['backend_policy_sha256']!=judge_policy().sha256 or sdk['policy_sha256']!=judge_policy().sha256
                    or sdk['text']!=reply['text'] or reply['model']!='gpt-6.1-sol'
                    or [sdk['input_tokens'],sdk['output_tokens']]!=calls[call]['actual']):raise ValueError
            else:
                from direct_deepseek_client import ACCEPTED_MODELS
                if reply['model'] not in ACCEPTED_MODELS:raise ValueError
    except (OSError,KeyError,TypeError,ValueError):
        raise ValueError('Genuine matching pilot receipts, SDK policy, adjudicated comparison and settled usage required') from None


class RetainedJudgeClient(CodexModelClient):
    """Changing effort must not refill the original Codex Judge claim bound."""
    def validate_output_limit(self,max_output_tokens: int) -> None:
        super().validate_output_limit(max_output_tokens)
        folder=self.state/'.agent/runs/monopoly-game-lobby/model-calls'
        count=0
        for path in folder.glob('*.json'):
            record=json.loads(path.read_bytes());identity=record['identity']
            if identity.get('role')!='judge' or identity.get('worker_backend')!='codex_app_server':continue
            key=sha256(identity['call_id'].encode()).hexdigest()
            if (self.state/'codex-claims'/identity['backend_policy_sha256']/(key+'.json')).exists():count+=1
        if count>=self.policy.max_calls:raise ModelError('Original cumulative Codex Judge claim bound reached; no policy reset')



def clients(framework: Path,root: Path,state: Path,budget: BudgetLedger,*,pilot: bool=False) -> tuple[AIConfig,list,DirectDeepSeekClient]:
    profile=role_profile();grant=json.loads((state/profile['authorization_ref']).read_bytes())
    if (grant.get('authority')!='explicit_user_session' or grant.get('profile_sha256')!=profile_sha256()
        or grant.get('limits')!=budget.limits or budget.limits!=profile['limits']
        or grant.get('judge_policy_sha256')!=judge_policy().sha256
        or grant.get('pilot_authorized') is not True):raise ModelError('Matching mixed-provider authorization required')
    if not pilot:
        active_qualification(state,budget._read()['calls'])
    config=load_direct_config(framework/'ai.local.toml')
    coder=DirectDeepSeekClient(config.api_key,state=state,cap=config.max_output_tokens or 65536)
    optimizer=DirectDeepSeekClient(config.api_key,state=state,purpose='context_optimizer',cap=8192)
    working=root/'codex-workers/production'
    if working.is_symlink():raise ModelError('Worker path must not be linked')
    working.mkdir(parents=True,exist_ok=True)
    if any(working.iterdir()):raise ModelError('Preserve unexpected worker-root contents')
    policy=judge_policy()
    judge=RetainedJudgeClient(policy,state,working,exchange=CodexStdioExchange(max_timeout_seconds=600),
        authorize=lambda digest:digest==grant['judge_policy_sha256'],timeout=180,session_timeout=600)
    return AIConfig(coder.config,judge.config),[coder,judge],optimizer
