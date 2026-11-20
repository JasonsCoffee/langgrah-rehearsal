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
if previous_version!=47 or result['candidate_revision']!='0cb5a37902f51bae2fa4c7dc2baef549a50fa487':raise ValueError('Exact cycle-47 dossier required')
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
for finding in dossier['failed_units']:
    unit=next(u for u in current['units'] if u['id']==finding['id'])
    if unit['role']!='test':raise ValueError('Implementation rework needs explicit Architect diagnosis')
    note=next(p for p in unit['owns'] if p.endswith('.cs')).removesuffix('.cs')+'.repair-v'+str(version)+'.md'
    guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    unit['owns'] += [note,note+'.meta']
    unit['instructions']+=' Current cycle '+str(version)+' MUST repair these latest actual independent source-review findings in the owned C# (still not globally frozen): '+finding['hypothesis']+' Preserve all effective assertions and update the current acceptance map truthfully. Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Do not return only notes.'
    if version==10 and unit['id']=='TEST-PRES-NFR':
        unit['instructions']+=' Prepared API clarification: LobbyShellBindings now declares public instance-owned Navigator (jj.WidgetSDK.Runtime.INavigator) and UserDefault (jj.Core.Runtime.IUserDefault) injection properties. Assign your independent recording services to those supported properties; assert actual calls with correct VM identity and account-scoped keys. Their runtime behavior remains nonfunctional and is delegated to SHELL. Do not reject the baseline merely because the injected properties do not yet cause side effects.'
if {u['id'] for u in dossier['failed_units']}!={'TEST-CHAT'}:raise ValueError('Exact Chat observation rework required')
(spec/'chat-observation.v48.md').write_bytes(Path(__file__).with_name('chat-observation.v48.md').read_bytes())
world='Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs'
p=source/world;t=p.read_text(encoding='utf-8');m='        public Action<string, string, string> NotificationEmitted;';assert t.count(m)==1 and 'UnreadSnapshotRead' not in t
p.write_text(t.replace(m,m+'\n        public Action<string> UnreadSnapshotRead;'),encoding='utf-8',newline='')
social='Runtime/Script/UI/LobbyRehearsal/LobbySocial.cs'
p=source/social;t=p.read_text(encoding='utf-8');m='        public int RequestFriendInvocations { get; private set; }';assert t.count(m)==1 and 'event Action<string> UnreadChanged' not in t
p.write_text(t.replace(m,m+'\n        public event Action<string> UnreadChanged;'),encoding='utf-8',newline='')
ports='Runtime/Script/UI/LobbyRehearsal/LobbyPorts.cs'
p=source/ports;t=p.read_text(encoding='utf-8');m='        LobbyUnread Unread(string accountId);';assert t.count(m)==1
p.write_text(t.replace(m,'        event System.Action<string> UnreadChanged;\n'+m),encoding='utf-8',newline='')
profile=json.loads((source/current['coding_profile_ref']['path']).read_bytes())
for rule in profile['rules']:
    if rule['path'] in (world,ports):rule['sha256']=sha256((source/rule['path']).read_bytes()).hexdigest()
profile_path='specs/monopoly-game-lobby/coding-profile.unread-v48.json'
(source/profile_path).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
current['coding_profile_ref']={'path':profile_path,'sha256':sha256((source/profile_path).read_bytes()).hexdigest()}
unit=next(u for u in current['units'] if u['id']=='TEST-CHAT')
unit['instructions']='Repair the actual remaining Chat presentation findings with chat-observation.v48.md and retained chat-presentation.v46.md. New nonfunctional boundaries: World.UnreadSnapshotRead and Social.UnreadChanged let you observe actual UI shared acquisition without source-name regex. Test handlers record only; never manufacture snapshots, outcomes or UI. Implement assertions in all five mapped C# methods, preserve valid helpers/cross-partial signatures, and update the current clause map. Delete invalid stronger/vacuous oracles identified in the real dossier: '+dossier['failed_units'][0]['hypothesis']+' Write newly owned repair-v48 note and prescribed metadata. Expected stub failures are required TDD, not a reason to defer writing tests. Read-only recording UI lifecycle is not yours to alter.'
next(u for u in current['units'] if u['id']=='SOCIAL')['instructions']+=' Prepared declaration-only unread boundaries in chat-observation.v48.md: invoke world.UnreadSnapshotRead(accountId) exactly once per actual Unread entry; raise UnreadChanged(accountId) after actual relevant delivery/read/friend-request unread mutations. Never emit manufactured outcomes. All counter separation and account rules remain.'
next(u for u in current['units'] if u['id']=='SHELL')['instructions']+=' Follow chat-observation.v48.md: subscribe and unsubscribe actual Social.UnreadChanged, read a coherent shared snapshot for active-account UI updates and reuse it across entry/channel badges; no separate quiet-period polling. Use optional UiClockSeconds for actual action-linked transitions and Refresh progression, without controller-name assumptions. All behavior remains delegated.'
git(source,'add',world,social,ports)
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
