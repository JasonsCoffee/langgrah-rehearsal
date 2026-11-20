"""Apply the explicit double grant at native budget abandonment, retaining freeze."""
from dataclasses import asdict
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets
from frozen_budget_continuation import check_contract_continuity,check_frozen_sources
from operational_transport import retained_run_reservations
from overlay_host import OverlayHost
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.recovery import TokenRecoveryGrant,recover_abandoned_run
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    if result.get('outcome')!='abandon' or result.get('reason')!='budget' or result['contract_version']!=66:
        raise ValueError('Exact native cycle-66 budget abandonment required')
    approval=json.loads((state/'budget-amendments/double-v66-user-approval.json').read_bytes())
    if approval['reply']!='Double those ceilings':raise ValueError('Explicit grant missing')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    if [policy['input_limit'],policy['output_limit'],policy['max_cycles'],policy['max_added_units']]!=[125000000,12000000,80,2]:
        raise ValueError('Unexpected prior limits')
    prior_raw=(run/'services-v66/state.json').read_bytes();prior=json.loads(prior_raw)
    frozen=prior['tdd']['frozen']
    if not frozen or len(frozen)!=189:raise ValueError('Global freeze must survive recovery')
    proof=json.loads((run/'abandon-v66.json').read_bytes());candidate=result['candidate_revision']
    if git(root/'module','rev-parse',proof['branch']).decode().strip()!=candidate:raise ValueError('Retained branch changed')
    source=root/'worktrees/architect-v67'
    if source.exists():raise ValueError('Preserve existing recovery preparation; reconcile explicitly')
    for path,digest in frozen.items():
        if sha256(git(root/'module','show',candidate+':'+path)).hexdigest()!=digest:
            raise ValueError('Retained candidate changed a frozen input: '+path)
    prepared_baseline='e1afab81deee0958d7b96373cd46369e337df45c'
    git(root/'module','worktree','add','-b','codex/lobby-architect-v67',str(source),prepared_baseline)
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v66.json').read_bytes();old=json.loads(old_raw)
    current=old|{'contract_version':67,'previous_contract_sha256':sha256(old_raw).hexdigest()}
    check_contract_continuity(old,current,sha256(old_raw).hexdigest())
    (spec/'contract.v67.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    rules=UnityAdapter();contracts=[]
    for n in range(1,68):
        contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=160))
    contract=contracts[-1]
    load_profile((source/contract.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),
        test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contract)
    git(source,'add','specs/monopoly-game-lobby/contract.v67.json')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Continue frozen lobby under approved double aggregate input ceiling')
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=125000000,output_limit=12000000,max_cycles=80,max_added_units=2)
    grant=TokenRecoveryGrant('lobby-double-v66','human-user','recovery-authorizations/double-v66.json',
        'monopoly-game-lobby',contracts[-2].sha256,sha256(result_raw).hexdigest(),160,250000000,24000000)
    authorization={'grant':asdict(grant),'authority':'explicit_user_session','approval':approval,'human_acceptance_granted':False}
    manifest={'kind':'doubled_budget','version':67,'recovery_id':grant.recovery_id,'previous_services_sha256':sha256(prior_raw).hexdigest(),'frozen':frozen}
    for name,digest in {'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
                        'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}.items():
        # Compare the trusted sources against the recorded rehearsal identities.
        if sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:raise ValueError('Trusted overlay changed')
    def reconciled() -> bool:
        retained_run_reservations(state,budget._read())
        check_frozen_sources(source,frozen)
        return json.loads((run/'services-v66/effects/transaction.json').read_bytes())['complete'] is True
    def candidate_reconciled(value: str) -> bool:
        old_workspace=root/'worktrees'/proof['workspace']
        return (value==candidate==proof['candidate_revision'] and proof['state']=='complete'
            and git(root/'module','rev-parse',proof['branch']).decode().strip()==candidate
            and git(old_workspace,'rev-parse','HEAD').decode().strip()==proof['restored_revision']
            and not git(old_workspace,'branch','--show-current').strip() and not git(old_workspace,'status','--porcelain')
            and not git(source,'status','--porcelain'))
    lease=RunLease(state,'monopoly-game-lobby','recovery-double-'+str(os.getpid()));host=OverlayHost()
    lease.acquire(owner_alive=lambda _:True);host.lease.acquire(owner_alive=lambda _:True)
    try:
        host.preflight();overlay=host.overlay.read();host.overlay.assert_ready(overlay['candidate'])
        atomic_write(state,grant.provenance,json.dumps(authorization,indent=2).encode())
        credential=secrets.token_urlsafe(32);digest=sha256(credential.encode()).digest()
        def authenticate(value: str) -> TokenRecoveryGrant | None:
            return grant if (hmac.compare_digest(sha256(value.encode()).digest(),digest)
                and json.loads((state/grant.provenance).read_bytes())==authorization) else None
        recover_abandoned_run(framework,state,'monopoly-game-lobby',contracts[-2],contract,context,budget,lease,
            credential=credential,authenticate=authenticate,workers_reconciled=reconciled,candidate_reconciled=candidate_reconciled)
        atomic_write(state,'frozen-continuations/v67.json',json.dumps(manifest,sort_keys=True).encode())
        atomic_write(state,'recovery-authorizations/budget-policy-before-double.json',json.dumps(policy,indent=2).encode())
        policy.update(input_limit=250000000,output_limit=24000000,max_cycles=160)
        atomic_write(state,'budget-policy.json',json.dumps(policy,indent=2).encode())
        active={'version':67,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v67','contract_sha256':contract.sha256}
        owned={u.id:list(u.owns) for u in contract.units if u.role=='impl' and u.status=='active'}
        proposals={u:{p:sha256(git(root/'module','show',candidate+':'+p)).hexdigest() for p in paths} for u,paths in owned.items()}
        prior_evidence=json.loads((run/'services-v66/evidence/v66-step12-verify.json').read_bytes())
        descriptor={'state':'complete','recovery_id':grant.recovery_id,'baseline':prepared_baseline,
            'retained_candidate':candidate,'owned':owned,'tests':frozen,'retained_proposals':proposals,
            'previous_evidence':prior_evidence,
            'note':'The exact proven pre-Green baseline is restored. Reapply your COMPLETE retained paid implementation and repair the supplied actual prior failures within your ownership. Preserve all workflows, frozen tests and configuration. The prior full candidate compiled; historical compiler diagnostics were already repaired. Actual remaining failures include geometry, rendered labels, interactions and persistence. Do not return a partial implementation or discard previously completed workflows.'}
        atomic_write(state,'baseline-restorations/v67.json',json.dumps(descriptor,indent=2).encode())
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        evidence=active|{'limits':budget.limits,'preserved_usage':budget.totals(),'frozen_count':len(frozen),
            'retained_candidate':candidate,'original_host_files':len(overlay['baseline']),
            'baseline_sha256':overlay['baseline_sha256'],'human_accepted':False}
        atomic_write(state,'recovery-authorizations/recovery-applied-double.json',json.dumps(evidence,indent=2).encode())
        print(json.dumps(evidence),flush=True)
    finally:host.lease.release();lease.release()


if __name__=='__main__':main()
