"""Resume the same run after a completed native preparation budget stop."""
from dataclasses import asdict
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets

from frozen_budget_continuation import check_frozen_sources, protected_tests
from lobby_budget_period import EXTENSION_50_ID as EXTENSION_ID, EXTENSION_50_REF as EXTENSION_REF, EXTENSION_50_REPLY as EXTENSION_REPLY, period_usage
from operational_transport import retained_run_reservations
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.recovery import TokenRecoveryGrant, recover_abandoned_run
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    framework = Path.cwd().resolve()
    root = Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state, module = root/'trusted-state', root/'module'
    run_id = 'monopoly-game-lobby'
    run = state/'.agent/runs'/run_id
    raw = (run/'result.json').read_bytes()
    result = json.loads(raw)
    if (result['outcome'], result['reason'], result['contract_version']) != ('abandon','budget',80):
        raise ValueError('Wait for the completed cycle-80 native budget stop')
    service = run/'services-v80'
    transaction = json.loads((service/'effects/transaction.json').read_bytes())
    service_state = json.loads((service/'state.json').read_bytes())
    if transaction['stage'] != 'prepare' or not transaction['complete'] or service_state['tdd']['frozen']:
        raise ValueError('This recovery carries a reconciled preparation boundary only')
    policy = json.loads((state/'budget-policy.json').read_bytes())
    budget = BudgetLedger(state,run_id,input_limit=policy['input_limit'],output_limit=policy['output_limit'],
                          max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    before = budget._read()
    period_usage(state,before)
    proof = json.loads((run/'abandon-v80.json').read_bytes())
    candidate = result['candidate_revision']
    integration = root/'worktrees'/proof['workspace']
    previous_source = root/'worktrees/architect-v80'
    source = root/'worktrees/architect-v81'
    old_manifest = json.loads((state/'frozen-continuations/v80.json').read_bytes())
    protected = {path:old_manifest['frozen'][path] for path in protected_tests(state,previous_source,80)}
    restoration = json.loads((state/'baseline-restorations/v80.json').read_bytes())
    if protected != restoration['tests']:
        raise ValueError('Prior protected inventory changed')

    def candidate_reconciled(value: str) -> bool:
        return (value == candidate == proof['candidate_revision'] and proof['state'] == 'complete'
                and proof['contract_sha256'] == result['contract_sha256']
                and git(module,'rev-parse','refs/heads/'+proof['branch']).decode().strip() == value
                and git(integration,'rev-parse','HEAD').decode().strip() == proof['restored_revision']
                and not git(integration,'branch','--show-current').strip()
                and not git(integration,'status','--porcelain'))

    lease = RunLease(state,run_id,'period-50m-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        if not candidate_reconciled(candidate) or source.exists() or (state/EXTENSION_REF).exists():
            raise ValueError('Preserve existing recovery preparation and reconcile explicitly')
        retained_run_reservations(state,before)
        git(module,'worktree','add','-b','codex/lobby-architect-v81',str(source),candidate)
        check_frozen_sources(source,protected)
        spec = source/'specs/monopoly-game-lobby'
        previous_raw = (spec/'contract.v80.json').read_bytes()
        if sha256(previous_raw).hexdigest() != result['contract_sha256']:
            raise ValueError('Previous contract changed')
        revised = json.loads(previous_raw)|{'contract_version':81,'previous_contract_sha256':result['contract_sha256']}
        from frozen_budget_continuation import vip_retry_first
        revised['units'] = vip_retry_first(revised['units'])
        relative_contract = 'specs/monopoly-game-lobby/contract.v81.json'
        (source/relative_contract).write_text(json.dumps(revised,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        contracts = []
        rules = UnityAdapter()
        for version in range(1,82):
            contracts.append(load_contract((spec/f'contract.v{version}.json').read_bytes(),source,rules,
                            previous=contracts[-1] if contracts else None,max_cycles=120))
        git(source,'add','--',relative_contract)
        git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid',
            'commit','-m','Continue authorized scopes after native budget recovery')
        context = discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
                                   sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
        grant = TokenRecoveryGrant(EXTENSION_ID,'human-user',EXTENSION_REF,run_id,contracts[-2].sha256,
                                   sha256(raw).hexdigest(),120,budget.limits[0]+10000000,budget.limits[1])
        approval = {'authority':'explicit_user_session','reply':EXTENSION_REPLY,'grant':asdict(grant)}
        atomic_write(state,EXTENSION_REF,json.dumps(approval,indent=2).encode())
        credential = secrets.token_urlsafe(32)

        def authenticate(value: str) -> TokenRecoveryGrant | None:
            if hmac.compare_digest(value,credential) and json.loads((state/EXTENSION_REF).read_bytes()) == approval:
                return grant
            return None

        def workers_reconciled() -> bool:
            check_frozen_sources(source,protected)
            return budget._read() == before and not git(source,'status','--porcelain')

        recover_abandoned_run(framework,state,run_id,contracts[-2],contracts[-1],context,budget,lease,
                             credential=credential,authenticate=authenticate,workers_reconciled=workers_reconciled,
                             candidate_reconciled=candidate_reconciled)
        after = budget._read()
        if after['calls'] != before['calls']:
            raise ValueError('Native recovery changed historical charges')
        atomic_write(state,'frozen-continuations/v81.json',json.dumps({
            'kind':'period_50m_scoped_recovery','version':81,'frozen':protected,
            'recovery_id':EXTENSION_ID,'prior_candidate':candidate},indent=2).encode())
        atomic_write(state,'baseline-restorations/v81.json',json.dumps(restoration,indent=2).encode())
        policy['input_limit'] = grant.input_limit
        atomic_write(state,'budget-policy.json',json.dumps(policy,indent=2).encode())
        active = {'version':81,'candidate':git(source,'rev-parse','HEAD').decode().strip(),
                  'contract_source':'architect-v81','contract_sha256':contracts[-1].sha256}
        usage, _ = period_usage(state,after)
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'token_period_usage':usage,'limits':budget.limits}),flush=True)
    finally:
        lease.release()


if __name__ == '__main__':
    main()
