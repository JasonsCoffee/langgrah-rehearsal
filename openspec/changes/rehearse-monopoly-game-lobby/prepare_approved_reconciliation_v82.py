"""Native transition preserving admitted repairs with method-bounded authoring."""
from hashlib import sha256
import json
import os
from pathlib import Path
from approved_test_reconciliation_v82 import PREVIOUS_SHA,SCOPE,author_paths,validate_revision
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
    module=root/'module';state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result_raw=(run/'result.json').read_bytes();result=json.loads(result_raw)
    if (result['outcome']!='rework' or result['contract_version']!=81 or result['contract_sha256']!=PREVIOUS_SHA
        or result['candidate_revision']!='167e8282aea7d81d86312dc132248dbf853d31fe'):
        raise ValueError('Exact cycle-81 VIP rework required')
    previous=(state/'frozen-continuations/v81.json').read_bytes();frozen=json.loads(previous)['frozen']
    prior=(run/'services-v81/state.json').read_bytes();dossier=(run/'dossier-v81.json').read_bytes()
    if not frozen or json.loads(prior)['tdd']['frozen']:
        raise ValueError('Original global freeze and no premature new freeze required')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],
        max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    period_usage(state,budget._read());retained_run_reservations(state,budget._read())
    source=root/'worktrees/architect-v82'
    if source.exists():raise ValueError('Preserve existing preparation')
    git(module,'worktree','add','-b','codex/lobby-architect-v82',str(source),result['candidate_revision'])
    check_frozen_sources(source,frozen)
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v81.json').read_bytes()
    old=json.loads(old_raw);current=json.loads(old_raw)
    current.update(contract_version=82,previous_contract_sha256=PREVIOUS_SHA)
    unit=next(u for u in current['units'] if u['id']=='TEST-VIP')
    paths=author_paths(unit['id']);guid=sha256(paths[1].encode()).hexdigest()[:32]
    unit['owns']+=list(paths[1:])
    unit['instructions']+=(
        '\nCycle 82 continues the exact prior approval. Modify only AssertRulesRowsForLevels '
        'and ContainsDistinctAmountField. Reject VIP2 充值说明；记录编号3000 and VIP2:3000积分. '
        'Accept VIP2：3000 and VIP2 累计充值：3000分 when 3000 is the configured amount, '
        'with equivalent spacing, punctuation and recognized recharge labels. Validate the entire '
        'threshold field adjacent to the VIP level: allow only recognized amount labels, '
        'separators, amount token and appropriate optional currency unit. Do not accept '
        'arbitrary recharge substrings or a later numeric field. Retain the substantive '
        'six-month recharge remark check and every existing unrelated assertion. '
        'Write '+paths[1]+' with the cases checked and '+paths[2]+
        ' with fileFormatVersion: 2 newline guid: '+guid+' newline. Prior notes remain unchanged.')
    validate_revision(old,current)
    (spec/'contract.v82.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    contracts=[];rules=UnityAdapter()
    for n in range(1,83):
        contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=120))
    git(source,'add','specs/monopoly-game-lobby/contract.v82.json')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Continue the approved VIP amount-field repair')
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    manifest={'kind':'approved_test_reconciliation_v82','version':82,'scope':SCOPE,'frozen':frozen,
        'previous_manifest_sha256':sha256(previous).hexdigest(),
        'previous_services_sha256':sha256(prior).hexdigest(),'previous_result_sha256':sha256(result_raw).hexdigest(),
        'dossier_sha256':sha256(dossier).hexdigest(),'human_accepted':False}
    restoration=json.loads((state/'baseline-restorations/v81.json').read_bytes())
    restoration['tests']={p:h for p,h in frozen.items() if p not in {item['path'] for item in SCOPE.values()}}
    def reconciled() -> bool:
        check_frozen_sources(source,frozen)
        return json.loads((run/'services-v81/effects/transaction.json').read_bytes())['complete'] is True and not git(source,'status','--porcelain')
    lease=RunLease(state,'monopoly-game-lobby','approved-reconciliation-v82-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'frozen-continuations/v82.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v82.json',json.dumps(restoration,indent=2).encode())
        active={'version':82,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v82','contract_sha256':contracts[-1].sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'token_period_usage':period_usage(state,budget._read())[0],
            'protected_original_files':len(restoration['tests']),'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
