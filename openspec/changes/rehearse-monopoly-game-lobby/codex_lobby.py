"""Trusted, explicitly authorized Codex composition for the retained lobby run."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.ai_models import AIConfig
from unity_coder.core.codex_backend import CodexModelClient, CodexPolicy
from unity_coder.core.codex_stdio import CodexStdioExchange
from unity_coder.core.ownership import confined_path
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

PRODUCTION_TIMEOUT_SECONDS=180


def validate_activation(raw: bytes, profile: dict, grant: dict, pilot: dict, limits: list[int]) -> None:
    """A proposal or successful transport alone grants no production authority."""
    digest=sha256(raw).hexdigest()
    outputs=pilot.get('outputs',{})
    plan=pilot.get('canonical_plan_sha256')
    if (grant.get('authority')!='explicit_user_session' or not grant.get('provenance')
        or grant.get('profile_sha256')!=digest
        or grant.get('permit_dispatch_accounting') is not True
        or grant.get('permit_activation_after_verified_pilot') is not True
        or pilot.get('profile_sha256')!=digest
        or pilot.get('retained_candidate')!=profile['candidate_revision']
        or pilot.get('contract_sha256')!=profile['contract_sha256']
        or pilot.get('human_acceptance_granted') is not False
        or outputs.get('coder',{}).get('value')!='HELLO LOBBY'
        or outputs.get('judge',{}).get('valid') is not True
        or not plan or any(outputs.get(r,{}).get('plan_sha256')!=plan for r in ('coder','judge'))
        or profile['roles']['coder']['model']==profile['roles']['judge']['model']
        or limits!=profile['preserve_aggregate_limits']):
        raise ValueError('Exact explicit Codex approval and verified independent pilot required')


def clients(root: Path, state: Path, budget):
    """Select new clients without editing the existing local provider config."""
    raw=Path(__file__).with_name('codex-backend.proposed.json').read_bytes()
    profile=json.loads(raw)
    grant=json.loads(confined_path(state,profile['authorization_ref']).read_bytes())
    pilot=json.loads((state/'codex-backend/pilot-verified-v60.json').read_bytes())
    validate_activation(raw,profile,grant,pilot,budget.limits)
    ledger=budget._read();run=state/'.agent/runs/monopoly-game-lobby/model-calls'
    working=root/'codex-workers/production'
    if working.is_symlink() or (working.exists() and any(working.iterdir())):
        raise ValueError('Preserve unexpected worker-root contents')
    working.mkdir(parents=True,exist_ok=True)
    result=[]
    for role in ('coder','judge'):
        chosen=profile['roles'][role]
        policy=CodexPolicy(role,chosen['model'],chosen['effort'],profile['budget_enforcement'],
            profile['authorization_ref'],profile['max_calls_per_role'],profile['framing_tokens'])
        call='codex-backend-pilot-v60-'+role
        receipt=json.loads((run/(sha256(call.encode()).hexdigest()+'.json')).read_bytes())
        sdk=json.loads((state/'codex-receipts'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes())
        if (pilot['roles'][role]!={'policy':asdict(policy),'sha256':policy.sha256}
            or receipt['identity'].get('backend_policy_sha256')!=policy.sha256
            or json.loads(receipt['reply']['text'])!=pilot['outputs'][role]
            or sdk['text']!=receipt['reply']['text']
            or [sdk['input_tokens'],sdk['output_tokens']]!=ledger['calls'][call].get('actual')
            or receipt['reply']['model']!=policy.model
            or sdk['policy_sha256']!=policy.sha256):
            raise ValueError('Pilot lacks matching actual Codex usage and independent receipts')
        client=CodexModelClient(policy,state,working,exchange=CodexStdioExchange(),
            authorize=lambda digest,expected=policy.sha256:digest==expected,
            timeout=PRODUCTION_TIMEOUT_SECONDS)
        result.append(client)
    return AIConfig(result[0].config,result[1].config),result


def reconcile(state,contract,budget,services,integration,settings,workers):
    """Native resume, retaining the actual admitted paid Chat State source."""
    from operational_transport import retained_run_reservations
    from full_file_admission import admitted_full_file
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    if (contract.contract_version!=60
        or contract.sha256!='5597cb71b2157b83cb4ee618133ba0cf9d708de54542479474f712173d1e7012'
        or result['outcome']!='operational'
        or result['candidate_revision']!='0519b568003ae4f820122ec8ef94016a068597f2'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v60-step4-prepare'
        or settings.coder.model!='gpt-6.2-sol' or settings.coder.effort!='low'
        or settings.judge.model!='gpt-6.1-sol' or settings.judge.effort!='medium'):
        raise ValueError('Exact Codex migration recovery identity changed')
    ledger=budget._read();retained=retained_run_reservations(state,ledger)
    if len(retained)!=16:raise ValueError('Historical uncertain reservations changed')
    unit=next(u for u in contract.units if u.id=='TEST-CHAT-STATE')
    admitted_full_file(state,60,'v60-step4-prepare',unit.id,unit.owns,
        result['candidate_revision'],integration,ledger,contract.sha256)
    if services.tdd.state(unit.id).preparation_attempts!=1:
        raise ValueError('Preparation count changed')
    hashes={p:sha256((integration/p).read_bytes()).hexdigest() for p in unit.owns}
    workers.reconciled_worker_patch={'unit':unit.id,
        'operation':'v60-step5-prepare-TEST-CHAT-STATE-TEST-CHAT-STATE',
        'source_sha256':hashes,'files':{},
        'reason':'Reuse admitted paid author source after backend migration; actual independent Codex Judge review required'}
    atomic_write(state,'recovery-authorizations/v60-codex-migration.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'retained_uncertain':retained,'usage':budget.totals(),'source_sha256':hashes,
        'roles':{'coder':settings.coder.model,'judge':settings.judge.model},
        'human_accepted':False,'next_judge_call':'v60-step5-prepare-review-TEST-CHAT-STATE'},indent=2).encode())
    return True


def retained_codex_call(state: Path, call: str, charge: dict, proof: dict) -> list[int]:
    """Never refund or replay an uncertain call; bind its original receipt/claim."""
    key=sha256(call.encode()).hexdigest()
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json')).read_bytes()
    receipt=json.loads(raw);identity=receipt['identity']
    claim=json.loads((state/'codex-claims'/identity['backend_policy_sha256']/(key+'.json')).read_bytes())
    if (proof.get('receipt_sha256')!=sha256(raw).hexdigest() or proof.get('charge')!=charge
        or 'actual' in charge or 'reply' in receipt or 'failure' not in receipt
        or identity.get('worker_backend')!='codex_app_server' or identity.get('provider')!='codex'
        or identity.get('call_id')!=call or charge.get('unit')!=identity.get('unit_id')
        or not call.startswith('v'+str(charge['version'])+'-')
        or claim!={'operation_id':call,'policy_sha256':identity['backend_policy_sha256'],
                   'prompt_sha256':identity['prompt_sha256']}
        or len(charge.get('reserved',[]))!=2
        or any(type(n) is not int or n<=0 for n in charge['reserved'])):
        raise ValueError('Uncertain Codex usage must retain its exact original claim and reservation')
    return charge['reserved']


def reconcile_timeout(state,contract,budget,services,integration,settings):
    """Continue with a new operation after the first production dispatch stopped."""
    from operational_transport import retained_run_reservations
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes());transaction=services.effects.read('transaction')
    call='v60-step6-prepare-TEST-CHAT-STATE-TEST-CHAT-STATE'
    worker=services.effects.read('worker-'+call)
    if (contract.contract_version!=60 or contract.sha256!='5597cb71b2157b83cb4ee618133ba0cf9d708de54542479474f712173d1e7012'
        or result['outcome']!='operational' or result['candidate_revision']!='0519b568003ae4f820122ec8ef94016a068597f2'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v60-step6-prepare'
        or not worker or 'result' in worker
        or settings.coder.model!='gpt-6.2-sol' or settings.judge.model!='gpt-6.1-sol'):
        raise ValueError('Exact Codex failed-dispatch recovery identity changed')
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=17:raise ValueError('All seventeen uncertain reservations must remain')
    atomic_write(state,'recovery-authorizations/v60-codex-deadline-resume.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'retained_uncertain':retained,'usage':budget.totals(),'production_timeout_seconds':PRODUCTION_TIMEOUT_SECONDS,
        'pilot_timeout_seconds':60,'prior_call_replayed':False,'human_accepted':False},indent=2).encode())
    return True
