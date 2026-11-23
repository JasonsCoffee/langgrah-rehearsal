"""Carry the unchanged approved scope after fixing mandatory Judge context."""
from hashlib import sha256
import json
import os
from pathlib import Path
from frozen_budget_continuation import check_frozen_sources
from lobby_budget_period import period_usage
from operational_transport import retained_run_reservations
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby';module=root/'module'
    result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    if (result['outcome']!='rework' or result['contract_version']!=71
        or result['contract_sha256']!='5821d5f37c45546f25b0a3bd6949784ddf695ae3d3f2d914019cb452d778493f'
        or result['candidate_revision']!='a3fe98c9115a6867d0fce23fbcb4cc3ec5f6335f'):
        raise ValueError('Exact unchanged-source cycle-71 rework required')
    previous_manifest=(state/'frozen-continuations/v71.json').read_bytes();manifest=json.loads(previous_manifest)
    prior_raw=(run/'services-v71/state.json').read_bytes();prior=json.loads(prior_raw)
    dossier_raw=(run/'dossier-v71.json').read_bytes()
    if prior['tdd']['frozen']:raise ValueError('Unexpected new global freeze')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],
        max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    period_usage(state,budget._read());retained_run_reservations(state,budget._read())
    source=root/'worktrees/architect-v72'
    if source.exists():raise ValueError('Preserve existing preparation')
    git(module,'worktree','add','-b','codex/lobby-architect-v72',str(source),result['candidate_revision'])
    check_frozen_sources(source,manifest['frozen'])
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v71.json').read_bytes()
    new=json.loads(old_raw)|{'contract_version':72,'previous_contract_sha256':sha256(old_raw).hexdigest()}
    (spec/'contract.v72.json').write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    contracts=[];rules=UnityAdapter()
    for n in range(1,73):
        contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=120))
    git(source,'add','specs/monopoly-game-lobby/contract.v72.json')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Carry approved test scope after mandatory review-context correction')
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    next_manifest={'kind':'carry_scoped_reconciliation_v71','version':72,'frozen':manifest['frozen'],
        'previous_manifest_sha256':sha256(previous_manifest).hexdigest(),
        'previous_result_sha256':sha256(result_raw).hexdigest(),'previous_services_sha256':sha256(prior_raw).hexdigest(),
        'dossier_sha256':sha256(dossier_raw).hexdigest(),'human_accepted':False}
    def reconciled() -> bool:
        check_frozen_sources(source,manifest['frozen'])
        tx=json.loads((run/'services-v71/effects/transaction.json').read_bytes())
        return tx['complete'] is True and not git(source,'status','--porcelain')
    lease=RunLease(state,'monopoly-game-lobby','carry-approved-v72-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'frozen-continuations/v72.json',json.dumps(next_manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v72.json',(state/'baseline-restorations/v71.json').read_bytes())
        active={'version':72,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v72','contract_sha256':contracts[-1].sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'token_period_usage':period_usage(state,budget._read())[0],'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
