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
if previous_version!=56 or result['candidate_revision']!='6462af7b64542757204f27b4592198f5b913d6b3':raise ValueError('Exact cycle-56 Records dossier required')
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
if {u['id'] for u in dossier['failed_units']}!={'TEST-RECORDS'}:raise ValueError('Exact Records observation rework required')
(spec/'records-observation.v57.md').write_bytes(Path(__file__).with_name('records-observation.v57.md').read_bytes())
view='Runtime/Script/UI/LobbyRehearsal/LobbyRehearsalViewBase.cs'
p=source/view;t=p.read_text(encoding='utf-8');m='        public TextMeshProUGUI Label;';assert t.count(m)==1 and 'RankLabel' not in t
fields='\n        public TextMeshProUGUI RankLabel;\n        public TextMeshProUGUI NameLabel;\n        public TextMeshProUGUI AmountLabel;\n        public TextMeshProUGUI ModeLabel;\n        public TextMeshProUGUI TierLabel;\n        public TextMeshProUGUI TimeLabel;\n        public TextMeshProUGUI IncomeLabel;\n        public TextMeshProUGUI ExpensesLabel;\n        public Graphic MedalGraphic;'
t=t.replace(m,m+fields);m='        public RectTransform SafeArea;';assert t.count(m)==1
t=t.replace(m,m+'\n        public RectTransform Overlay;\n        public TextMeshProUGUI OverlayText;\n        public ScrollRect OverlayScroll;\n        public GameObject LoadingIndicator;');p.write_text(t,encoding='utf-8',newline='')
dto='Runtime/Script/UI/LobbyRehearsal/LobbyDtos.cs'
p=source/dto;t=p.read_text(encoding='utf-8');m='    public sealed class LobbyRankingSnapshot';assert t.count(m)==1 and 'class LobbyRankingPage' not in t
extra='    public sealed class LobbyRankingPage\n    {\n        public DateTimeOffset TimeUtc;\n        public int Page;\n        public int TotalCount;\n        public bool HasMore;\n        public List<LobbyRankRow> Rows = new List<LobbyRankRow>();\n    }\n\n'
p.write_text(t.replace(m,extra+m),encoding='utf-8',newline='')
ports='Runtime/Script/UI/LobbyRehearsal/LobbyPorts.cs'
p=source/ports;t=p.read_text(encoding='utf-8');m='        LobbyRankingSnapshot Rankings(string accountId);';assert t.count(m)==1
sig='LobbyRankingPage RankingPage(string accountId, bool week, int page, int pageSize, System.DateTimeOffset snapshotUtc)'
p.write_text(t.replace(m,m+'\n        '+sig+';'),encoding='utf-8',newline='')
records='Runtime/Script/UI/LobbyRehearsal/LobbyRecordsSettings.cs'
p=source/records;t=p.read_text(encoding='utf-8');m='        public List<LobbyMatchRecord> History(string accountId, int page, int pageSize)';assert t.count(m)==1
p.write_text(t.replace(m,'        public '+sig+'\n        {\n            return new LobbyRankingPage();\n        }\n\n'+m),encoding='utf-8',newline='')
world='Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs'
p=source/world;t=p.read_text(encoding='utf-8');m='        public Action<string> UnreadSnapshotRead;';assert t.count(m)==1
p.write_text(t.replace(m,m+'\n        public Action<string, bool, int, int, DateTimeOffset> RankingPageRequested;'),encoding='utf-8',newline='')
profile=json.loads((source/current['coding_profile_ref']['path']).read_bytes())
for rule in profile['rules']:
    if rule['path'] in (view,dto,ports,world):rule['sha256']=sha256((source/rule['path']).read_bytes()).hexdigest()
profile_path='specs/monopoly-game-lobby/coding-profile.record-bindings-v57.json'
(source/profile_path).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
current['coding_profile_ref']={'path':profile_path,'sha256':sha256((source/profile_path).read_bytes()).hexdigest()}
unit=next(u for u in current['units'] if u['id']=='TEST-RECORDS')
unit['instructions']='Read records-observation.v57.md and records-oracles.v55.md. Repair all 24 mapped tests using actual typed row fields/overlays and fake RankingPage boundary. New declarations implement no outcomes; NEVER populate expected row refs, data, response DTOs or callbacks in test fixtures. Require exact active ranked/pinned/history identity and actual displayed typed cells, real medal graphics for ranks 1/2/3, fixed nonclipped pinned self geometry and exact standalone amounts. Use real RankingPage/HasMore/request trace for populated scroll/Next pagination and invalid backend page probes; History is not ranking evidence. Fix the actual financial/config/debt/music/quality/overlay/async errors in the dossier. Inputs must be independent and coherent; derived totals are not prefilled expected outputs. Await entry/open/shutdown and bounded pointer-command completion, preserving the one-street lifetime. All valid assertions/IDs and current maps remain. Actual dossier: '+dossier['failed_units'][0]['hypothesis']+' Write newly owned repair-v57 note/meta and truthful maps. Test-first strict hash-bound finite-helper output. No game business implementation.'
next(u for u in current['units'] if u['id']=='RECORDS')['instructions']+=' Implement declared RankingPage and actual RankingPageRequested observation per records-observation.v57.md, using the captured shared snapshot, exact capped pages/HasMore and empty terminal/out-of-range pages. Preserve canonical fake ledger normalization and data persistence. Declarations contain no business behavior.'
next(u for u in current['units'] if u['id']=='SHELL')['instructions']+=' Follow records-observation.v57.md: bind actual typed rank/name/amount/history/detail/medal fields and explicit ranked/pinned-self/history roles; real separate fixed self row; actual Overlay/Text/Scroll/LoadingIndicator refs; Next/scroll requests use RankingPage and captured timestamp, no requests after termination. Effects and async lifecycle remain real delegated behavior. No diagnostic-only hidden fields or fabricated UI.'
git(source,'add',view,dto,ports,world,records)
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
