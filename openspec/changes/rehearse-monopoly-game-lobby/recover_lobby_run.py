"""Trusted import of the user's recovery authorization and native transition."""
from dataclasses import asdict
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets

from overlay_host import OverlayHost
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.recovery import RecoveryGrant, recover_abandoned_run
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve()
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state'
    prefix='.agent/runs/monopoly-game-lobby'
    run=state/prefix
    source=root/'worktrees/architect-v4'
    spec=source/'specs/monopoly-game-lobby'
    contracts=[]
    for version in (1,2,3,4):
        contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,UnityAdapter(),
            previous=contracts[-1] if contracts else None,max_cycles=6))
    previous,current=contracts[-2:]
    intent_path=run/'recoveries/lobby-extend-to-six.json'
    if intent_path.exists():
        intent=json.loads(intent_path.read_bytes())
        grant=RecoveryGrant(**intent['authorization'])
        result_raw=bytes.fromhex(intent['saved']['result.json'])
    else:
        result_raw=(run/'result.json').read_bytes()
        grant=RecoveryGrant('lobby-extend-to-six','human-user','recovery-authorizations/extend-to-six.json',
            'monopoly-game-lobby',previous.sha256,sha256(result_raw).hexdigest(),6)
    authorization={'grant':asdict(grant),'authority':'explicit user message in the active session',
        'request':'Ok, go ahead implement the safe recovery for abandoned runs. Then continue working towards awaiting_human_review.',
        'approved_proposal':'Extend total cycle ceiling from 3 to 6; preserve 3000000 input and 900000 output token ceilings, all usage and evidence.',
        'human_acceptance_granted':False}
    authpath=state/grant.provenance
    if authpath.exists() and json.loads(authpath.read_bytes())!=authorization:
        raise ValueError('Existing session authorization differs')
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    # Old selector is deliberate: native recovery reconciles old or fully
    # published amended ledger bytes after a crash. It never resets them.
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=3000000,output_limit=900000,max_cycles=3,max_added_units=2)
    lease=RunLease(state,'monopoly-game-lobby','recovery-'+str(os.getpid()))
    host=OverlayHost()
    lease.acquire(owner_alive=lambda _:True)
    host.lease.acquire(owner_alive=lambda _:True)
    try:
        host.preflight()
        overlay=host.overlay.read()
        host.overlay.assert_ready(overlay['candidate'])
        proof=json.loads((run/'abandon-v3.json').read_bytes())
        def candidate_reconciled(candidate: str) -> bool:
            old=root/'worktrees'/proof['workspace']
            if (candidate!=proof['candidate_revision'] or proof['state']!='complete'
                or git(root/'module','rev-parse',proof['branch']).decode().strip()!=candidate
                or git(old,'rev-parse','HEAD').decode().strip()!=proof['restored_revision']
                or git(old,'branch','--show-current').decode().strip()
                or git(old,'status','--porcelain') or git(source,'status','--porcelain')):
                return False
            git(source,'merge-base','--is-ancestor',candidate,'HEAD')
            return True
        def workers_reconciled() -> bool:
            ledger=json.loads((run/'budget.json').read_bytes())
            transaction=json.loads((run/'services-v3/effects/transaction.json').read_bytes())
            return (transaction.get('complete') is True and all('actual' in call for call in ledger['calls'].values()))
        atomic_write(state,grant.provenance,json.dumps(authorization,ensure_ascii=False,indent=2).encode())
        credential=secrets.token_urlsafe(32)
        digest=sha256(credential.encode()).digest()
        def authenticate(value: str) -> RecoveryGrant | None:
            if not hmac.compare_digest(sha256(value.encode()).digest(),digest):return None
            recorded=json.loads(authpath.read_bytes())
            return RecoveryGrant(**recorded['grant']) if recorded==authorization else None
        recover_abandoned_run(framework,state,'monopoly-game-lobby',previous,current,context,budget,lease,
            credential=credential,authenticate=authenticate,workers_reconciled=workers_reconciled,
            candidate_reconciled=candidate_reconciled)
        policy=json.loads((state/'budget-policy.json').read_bytes())
        before_policy=json.dumps(policy,sort_keys=True).encode()
        archive=state/'recovery-authorizations/budget-policy-before-six.json'
        if not archive.exists():atomic_write(state,archive.relative_to(state).as_posix(),before_policy)
        policy['max_cycles']=6
        atomic_write(state,'budget-policy.json',json.dumps(policy,indent=2).encode())
        candidate=git(source,'rev-parse','HEAD').decode().strip()
        active={'version':4,'candidate':candidate,'contract_source':'architect-v4','contract_sha256':current.sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        record={'run_id':'monopoly-game-lobby','recovery':grant.recovery_id,'contract_version':4,
            'contract_sha256':current.sha256,'baseline':candidate,'preserved_usage':budget.totals(),
            'limits':budget.limits,'retained_candidate':json.loads(result_raw)['candidate_revision'],
            'original_host_files':len(overlay['baseline']),'baseline_sha256':overlay['baseline_sha256'],
            'original_baseline_checked':True,'human_accepted':False}
        atomic_write(state,'recovery-authorizations/recovery-applied.json',json.dumps(record,indent=2).encode())
        (Path(__file__).parent/'evidence/recovery-applied.json').write_text(json.dumps(record,indent=2),encoding='utf-8',newline='')
        print(json.dumps(record))
    finally:
        host.lease.release()
        lease.release()


if __name__=='__main__':main()
