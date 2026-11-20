"""Prepare and transition an actual consecutive native rework, preserving usage."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid5,NAMESPACE_URL
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git
from operational_transport import retained_run_reservations, retained_coder_request_failure, retained_coder_connection_failure, retained_sol_review_failure, retained_transport_failure, retained_key_limit_failure, retained_calibration_failure, retained_tls_probe_failure

framework=Path.cwd().resolve()
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework':raise ValueError('Only actual native rework may transition')
previous_version=result['contract_version'];version=previous_version+1
policy=json.loads((state/'budget-policy.json').read_bytes())
if version>policy['max_cycles']:raise ValueError('Authorized cycle ceiling reached')
dossier=json.loads((run/('dossier-v'+str(previous_version)+'.json')).read_bytes())
source=root/'worktrees'/('architect-v'+str(version))
if source.exists():raise ValueError('Preserve existing preparation; no implicit replay')
git(root/'module','worktree','add','-b','codex/lobby-architect-v'+str(version),str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby'
old_path=spec/('contract.v'+str(previous_version)+'.json')
old=json.loads(old_path.read_bytes())
current=old|{'contract_version':version,'previous_contract_sha256':sha256(old_path.read_bytes()).hexdigest(),'ownership_migrations':[]}
if version==10:
    path=source/'Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs'
    text=path.read_text(encoding='utf-8')
    marker='        public ILobbyEntryPort EntryPort { get; set; }'
    if text.count(marker)!=1 or 'public jj.WidgetSDK.Runtime.INavigator Navigator' in text:
        raise ValueError('Unexpected prepared injection API shape')
    text=text.replace(marker,marker+'\n        public jj.WidgetSDK.Runtime.INavigator Navigator { get; set; }\n        public jj.Core.Runtime.IUserDefault UserDefault { get; set; }')
    path.write_text(text,encoding='utf-8',newline='')
    next(u for u in current['units'] if u['id']=='SHELL')['instructions']+=' Cycle 10 prepares nonfunctional Navigator and UserDefault injection properties. Production must bind the real framework dependencies to these instance-owned slots. Exercise all real screen routes through the supplied Navigator (including target VM identity) and persist/restore account-scoped settings through the supplied UserDefault; ILobbyUiPort remains the presentation observation boundary. Never manufacture observations or bypass these dependencies with static memory.'
if previous_version!=40 or version!=41 or {u['id'] for u in dossier['failed_units']}!={'TEST-SOCIAL'}:raise ValueError('Only actual peer-owned compilation dossier')
if 'ChatFocusInput' not in dossier['failed_units'][0]['hypothesis']:raise ValueError('Peer finding changed')
message=next(u for u in current['units'] if u['id']=='TEST-CHAT-MSG')
social=next(u for u in current['units'] if u['id']=='TEST-SOCIAL')
message['depends_on']=[p for p in message['depends_on'] if p!='TEST-SOCIAL']
social['depends_on']=list(dict.fromkeys(social['depends_on']+['TEST-CHAT-MSG']))
current['units'].remove(message);index=next(i for i,u in enumerate(current['units']) if u['id']=='TEST-HARNESS')+1;current['units'].insert(index,message)
note='Tests/Runtime/Script/LobbyRehearsal/LobbyChatMessageTests.repair-v41.md';guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
message['owns'] += [note,note+'.meta']
message['instructions']='You are the TEST AUTHOR for the four mapped message tests (L13-06,08,12,13) and exclusive helpers in your owned partial. Read preparation-order.v41.md and chat-authoring.v39.md. Fix the actual owned ChatFocusInput compilation defect first: TMP_InputField.onSelect takes a string, not BaseEventData; retain genuine pointer/input activation and keyboard request observations. Then strengthen all four mapped source clauses with successful and rejected bound deliveries, actual pending state using ChatDeliveryAllowed, failure/overlong draft preservation, both-channel Unicode boundaries, friend-only private delivery/history, literal text UI, configurable world cooldown and long-press confirmed/cancelled reporting. Expected assertions against production stubs are required TDD; never implement service outcomes in adapters. Consolidate effective companion checks into the mapped methods. All other partials are read-only. Return complete owned source and truthful changed notes through the bounded full-file protocol. Also write '+note+' with meta fileFormatVersion: 2 newline guid: '+guid+' newline. Preserve all valid assertions and correct invalid fixture oracles.'
missing={p:('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+p.removesuffix('.meta')).hex+'\n' if p.endswith('.md.meta') else 'Required owned file') for p in message['owns'] if not (source/p).exists()}
message['instructions']+=' Required currently missing owned files (write all; metadata template supplied): '+json.dumps(missing)
social['instructions']='Review/maintain only the ten mapped friend-list/UI methods and owned helpers. The independent cycle-40 failure was in read-only ChatFocusInput. TEST-CHAT-MSG now runs first and owns that repair; never edit its source. Existing blocked notes are truthful cycle-40 history and do not claim a pass. No new Social note or C# change is required merely for this scheduling revision. Preserve all genuine assertions, approved pagination and exact membership checks, account-local observations and source clauses. Read preparation-order.v41.md and current unit scope. If a new actual owned defect is found, repair only owned C# and update an existing owned map.'
(spec/'preparation-order.v41.md').write_bytes(Path(__file__).with_name('preparation-order.v41.md').read_bytes())
(spec/'preparation-order.v41.json').write_text(json.dumps({'reason':dossier['failed_units'][0]['hypothesis'],'owner_first':'TEST-CHAT-MSG','consumer':'TEST-SOCIAL','source_bodies_changed_by_architect':False,'rationale':'Shared helper declarations already exist, so owner authoring can read them before a new consumer review; the actual compiler defect must be repaired by its exclusive owner.'},indent=2)+'\n',encoding='utf-8',newline='')
(spec/('contract.v'+str(version)+'.json')).write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter();contracts=[]
for n in range(1,version+1):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=policy['max_cycles']))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
git(source,'add','specs/monopoly-game-lobby')
if version==10:git(source,'add','Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare consecutive delegated test repair cycle '+str(version))
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
def reconciled():
    retained_run_reservations(state,json.loads((run/'budget.json').read_bytes()))
    transaction=json.loads((run/('services-v'+str(previous_version))/'effects/transaction.json').read_bytes())
    if not transaction.get('complete') or git(source,'status','--porcelain'):return False
    return True
lease=RunLease(state,'monopoly-game-lobby','cycle-transition-'+str(os.getpid()))
lease.acquire(owner_alive=lambda _:True)
try:
    transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
    candidate=git(source,'rev-parse','HEAD').decode().strip()
    active={'version':version,'candidate':candidate,'contract_source':'architect-v'+str(version),'contract_sha256':contracts[-1].sha256}
    atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
    print(json.dumps(active|{'preserved_usage':budget.totals(),'limits':budget.limits,'human_accepted':False}))
finally:lease.release()
