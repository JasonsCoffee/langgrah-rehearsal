"""Authenticated session import for the approved cycle and token amendments."""
from dataclasses import asdict
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets
from overlay_host import OverlayHost
from operational_transport import retained_transport_failure
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.ai_models import load_ai_config
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.recovery import TokenRecoveryGrant,recover_abandoned_run
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

def main() -> None:
    framework=Path.cwd().resolve();directory=Path(__file__).parent
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    source=root/'worktrees/architect-v13';spec=source/'specs/monopoly-game-lobby'
    contracts=[]
    for version in range(1,14):
        contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,UnityAdapter(),previous=contracts[-1] if contracts else None,max_cycles=30))
    previous,current=contracts[-2:]
    intent_path=run/'recoveries/lobby-extend-thirty-12m.json'
    if intent_path.exists():
        intent=json.loads(intent_path.read_bytes())
        grant=TokenRecoveryGrant(**intent['authorization'])
        result_raw=bytes.fromhex(intent['saved']['result.json'])
    else:
        result_raw=(run/'result.json').read_bytes()
        grant=TokenRecoveryGrant('lobby-extend-thirty-12m','human-user','recovery-authorizations/extend-thirty-12m.json',
            'monopoly-game-lobby',previous.sha256,sha256(result_raw).hexdigest(),30,12000000,3600000)
    authorization={'grant':asdict(grant),'authority':'explicit user messages in the active session',
        'cycle_request':'Increase the cycle ceiling to 30 and continue the same run to awaiting_human_review. Preserve all usage, configured models, trusted overlay, and frozen-test rules. Don’t bypass the independent judge.',
        'token_question':'May I raise the totals to 12,000,000 input / 3,600,000 output, preserving every charge and reservation?',
        'token_reply':'Approve 12,000,000 / 3,600,000','human_acceptance_granted':False}
    authpath=state/grant.provenance
    if authpath.exists() and json.loads(authpath.read_bytes())!=authorization:raise ValueError('Existing authorization differs')
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=6000000,output_limit=1800000,max_cycles=12,max_added_units=2)
    for name,digest in {'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f','overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}.items():
        if sha256((directory/name).read_bytes()).hexdigest()!=digest:raise ValueError('Trusted overlay source changed')
    settings=load_ai_config(framework/'ai.local.toml')
    for role,config in (('coder',settings.coder),('judge',settings.judge)):
        receipts=sorted((run/'model-calls').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        identity=next(json.loads(p.read_bytes())['identity'] for p in receipts if json.loads(p.read_bytes())['identity']['role']==role)
        for key in ('model','provider','effort','temperature_mode','upstream_provider'):
            if getattr(config,key)!=identity.get(key,''):raise ValueError('Configured model policy changed: '+role+'/'+key)
    lease=RunLease(state,'monopoly-game-lobby','recovery-'+str(os.getpid()));host=OverlayHost()
    lease.acquire(owner_alive=lambda _:True);host.lease.acquire(owner_alive=lambda _:True)
    try:
        host.preflight();overlay=host.overlay.read()
        print('Checking original host baseline and managed imported candidate',flush=True)
        host.overlay.assert_ready(overlay['candidate'])
        proof=json.loads((run/'abandon-v12.json').read_bytes())
        def candidate_reconciled(candidate: str) -> bool:
            old=root/'worktrees'/proof['workspace']
            if (candidate!=proof['candidate_revision'] or proof['state']!='complete'
                or git(root/'module','rev-parse',proof['branch']).decode().strip()!=candidate
                or git(old,'rev-parse','HEAD').decode().strip()!=proof['restored_revision']
                or git(old,'branch','--show-current').decode().strip()
                or git(old,'status','--porcelain') or git(source,'status','--porcelain')):return False
            git(source,'merge-base','--is-ancestor',candidate,'HEAD');return True
        def workers_reconciled() -> bool:
            ledger=json.loads((run/'budget.json').read_bytes())
            for call_id,call in ledger['calls'].items():
                if 'actual' in call:continue
                if call_id!='v8-step3-prepare-review-TEST-PRES-CORE':return False
                receipt=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
                retained_transport_failure(receipt,call,8)
            return json.loads((run/'services-v12/effects/transaction.json').read_bytes()).get('complete') is True
        atomic_write(state,grant.provenance,json.dumps(authorization,ensure_ascii=False,indent=2).encode())
        credential=secrets.token_urlsafe(32);digest=sha256(credential.encode()).digest()
        def authenticate(value: str) -> TokenRecoveryGrant | None:
            if not hmac.compare_digest(sha256(value.encode()).digest(),digest):return None
            recorded=json.loads(authpath.read_bytes())
            return TokenRecoveryGrant(**recorded['grant']) if recorded==authorization else None
        recover_abandoned_run(framework,state,'monopoly-game-lobby',previous,current,context,budget,lease,
            credential=credential,authenticate=authenticate,workers_reconciled=workers_reconciled,candidate_reconciled=candidate_reconciled)
        policy=json.loads((state/'budget-policy.json').read_bytes())
        archive=state/'recovery-authorizations/budget-policy-before-thirty-12m.json'
        if not archive.exists():atomic_write(state,archive.relative_to(state).as_posix(),json.dumps(policy,sort_keys=True).encode())
        policy.update(max_cycles=30,input_limit=12000000,output_limit=3600000)
        atomic_write(state,'budget-policy.json',json.dumps(policy,indent=2).encode())
        candidate=git(source,'rev-parse','HEAD').decode().strip()
        active={'version':13,'candidate':candidate,'contract_source':'architect-v13','contract_sha256':current.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        record=active|{'run_id':'monopoly-game-lobby','recovery':grant.recovery_id,'preserved_usage':budget.totals(),
            'limits':budget.limits,'retained_candidate':json.loads(result_raw)['candidate_revision'],
            'original_host_files':len(overlay['baseline']),'baseline_sha256':overlay['baseline_sha256'],
            'original_baseline_checked':True,'human_accepted':False}
        atomic_write(state,'recovery-authorizations/recovery-applied-thirty-12m.json',json.dumps(record,indent=2).encode())
        (directory/'evidence/recovery-applied-thirty-12m.json').write_text(json.dumps(record,indent=2),encoding='utf-8',newline='')
        print(json.dumps(record),flush=True)
    finally:host.lease.release();lease.release()

if __name__=='__main__':main()
