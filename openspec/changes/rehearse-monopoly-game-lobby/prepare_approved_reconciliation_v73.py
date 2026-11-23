"""Native transition carrying both approvals with method-bounded authoring."""
from hashlib import sha256
import json
import os
from pathlib import Path
from approved_test_reconciliation_v73 import PREVIOUS_SHA,REPLY,CHAT,SCOPE,author_paths,validate_revision
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
    if (result['outcome']!='rework' or result['contract_version']!=72 or result['contract_sha256']!=PREVIOUS_SHA
        or result['candidate_revision']!='b7eecbeb35a7183c8b787daf9d5ba2508f0b2695'):
        raise ValueError('Exact cycle-72 unchanged-source rework required')
    previous=(state/'frozen-continuations/v72.json').read_bytes();frozen=json.loads(previous)['frozen']
    prior=(run/'services-v72/state.json').read_bytes();dossier=(run/'dossier-v72.json').read_bytes()
    old_approval=(state/'model-authorizations/test-reconciliation-v71.json').read_bytes()
    if len(frozen)!=199 or json.loads(prior)['tdd']['frozen']:
        raise ValueError('Original global freeze and no premature new freeze required')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],
        max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    period_usage(state,budget._read());retained_run_reservations(state,budget._read())
    source=root/'worktrees/architect-v73'
    if source.exists():raise ValueError('Preserve existing preparation')
    git(module,'worktree','add','-b','codex/lobby-architect-v73',str(source),result['candidate_revision'])
    check_frozen_sources(source,frozen)
    spec=source/'specs/monopoly-game-lobby';old_raw=(spec/'contract.v72.json').read_bytes()
    old=json.loads(old_raw);current=json.loads(old_raw)
    current.update(contract_version=73,previous_contract_sha256=PREVIOUS_SHA)
    unit=next(u for u in current['units'] if u['id']=='TEST-CHAT-MSG')
    paths=author_paths(unit['id']);guid=sha256(paths[1].encode()).hexdigest()[:32]
    unit['owns']+=list(paths[1:])
    unit['instructions']+='\nCYCLE 73 EXPLICIT USER-APPROVED CHAT ORACLE RECONCILIATION. Change ONLY the existing bodies of MsgAvatarSpritesForRow and MsgPermittedRowGraphics in LobbyChatMessageTests.cs. Resolve the delivered message by the actual row.RowEntityId and then its LobbyMessage.Sender; do not infer sender from account-name substrings in text. Allow actual row-background and avatar binding references only, validated against independent sender avatar data. Merely matching a sprite/texture is insufficient: an otherwise unknown attachment that reuses the avatar texture must remain rejected. Use actual serialized/runtime control roles and references, never object-name or texture-name guessing. Preserve both helper signatures, every other source byte and all four enabled mapped test bodies, including Unicode, literal rendering, scroll-content scoping, cooldown/draft and reporting cancellation/confirmation coverage. Do not implement game behavior or arrange fabricated coordinator state. Write '+paths[1]+' with exact source rationale and preserved coverage, and '+paths[2]+' exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Independent Judge review and fresh behavioral Red must precede the new global freeze.'
    validate_revision(old,current)
    (spec/'contract.v73.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    contracts=[];rules=UnityAdapter()
    for n in range(1,74):
        contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=120))
    git(source,'add','specs/monopoly-game-lobby/contract.v73.json')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare approved message-identity and avatar-role test repairs')
    context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),
        sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    manifest={'kind':'approved_test_reconciliation_v73','version':73,'scope':SCOPE,'frozen':frozen,
        'previous_manifest_sha256':sha256(previous).hexdigest(),'previous_approval_sha256':sha256(old_approval).hexdigest(),
        'previous_services_sha256':sha256(prior).hexdigest(),'previous_result_sha256':sha256(result_raw).hexdigest(),
        'dossier_sha256':sha256(dossier).hexdigest(),'human_accepted':False}
    restoration=json.loads((state/'baseline-restorations/v72.json').read_bytes())
    restoration['tests']={p:h for p,h in frozen.items() if p not in {item['path'] for item in SCOPE.values()}}
    def reconciled() -> bool:
        check_frozen_sources(source,frozen)
        return json.loads((run/'services-v72/effects/transaction.json').read_bytes())['complete'] is True and not git(source,'status','--porcelain')
    lease=RunLease(state,'monopoly-game-lobby','approved-reconciliation-v73-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        atomic_write(state,'model-authorizations/test-reconciliation-v73.json',json.dumps({
            'authority':'explicit_user_session','reply':REPLY,'version':73,'scope':{'TEST-CHAT-MSG':CHAT}},indent=2).encode())
        atomic_write(state,'frozen-continuations/v73.json',json.dumps(manifest,indent=2).encode())
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
        atomic_write(state,'baseline-restorations/v73.json',json.dumps(restoration,indent=2).encode())
        active={'version':73,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v73','contract_sha256':contracts[-1].sha256}
        atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
        print(json.dumps(active|{'token_period_usage':period_usage(state,budget._read())[0],
            'protected_original_files':len(restoration['tests']),'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
