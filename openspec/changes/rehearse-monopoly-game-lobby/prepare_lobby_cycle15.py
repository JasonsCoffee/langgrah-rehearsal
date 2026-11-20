"""Reconcile verified Shop preparation and approved handoff scope into rework."""
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
from operational_transport import retained_transport_failure

framework=Path.cwd().resolve();directory=Path(__file__).parent
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True);state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework' or result['contract_version']!=14:raise ValueError('Actual cycle-fourteen rework required')
if json.loads((run/'services-v14/state.json').read_bytes())['tdd']['frozen'] is not None:raise ValueError('Global freeze prohibits authoring repair')
source=root/'worktrees/architect-v15'
if source.exists():raise ValueError('Preserve existing preparation; reconcile explicitly')
asset=json.loads((state/'shop-preparation-v15/complete.json').read_bytes())
if asset['trusted_overlay_changed'] or asset['business_logic_written'] or asset['original_files_checked']!=81134:raise ValueError('Verified asset-only preparation required')
git(root/'module','worktree','add','-b','codex/lobby-architect-v15',str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby';old_path=spec/'contract.v14.json';old=json.loads(old_path.read_bytes())
current=old|{'contract_version':15,'previous_contract_sha256':sha256(old_path.read_bytes()).hexdigest(),'ownership_migrations':[]}
asset_paths=['Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/LobbyView_placeHolder.prefab','Editor/Script/LobbyRehearsal/LobbyShopPreparation.cs','Editor/Script/LobbyRehearsal/LobbyShopPreparation.cs.meta']
for path in asset_paths:atomic_write(source,path,git(root/'module','show',asset['candidate']+':'+path))
lobby=asset_paths[0]
if sha256((source/lobby).read_bytes()).hexdigest()!=asset['changed']['Assets/JJGame/monopoly/'+lobby]:raise ValueError('Captured Shop asset identity changed')
scope_path='specs/monopoly-game-lobby/approved-rehearsal-scope.v15.md'
(source/scope_path).write_bytes((directory/'approved-rehearsal-scope.v15.md').read_bytes())
conditions=json.loads((spec/'acceptance-conditions.v6.json').read_bytes())
for row in conditions:
    if row['story']=='US-L3-10':row['approved_rehearsal_disposition']='Full in-match locomotion and dismount rendering are deferred by the user-approved fake handoff scope; verify complete lobby vehicle parity, cosmetic-only observable values, and fake-match equip rejection. See approved-rehearsal-scope.v15.md; do not claim real-match rendering execution.'
    if row['story']=='US-L7-01':row['verified_preparation']='Dedicated serialized Lobby action Shop now exists beside the wallet, in addition to the contextual-menu route. Both entrances remain required.'
(spec/'acceptance-conditions.v15.json').write_text(json.dumps(conditions,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
observed=json.loads((spec/'presentation-observation.v5.json').read_bytes())
view=next(v for v in observed['views'] if v['screen']=='Lobby')
if 'Shop' in view['controls']:raise ValueError('Unexpected prior Shop observation')
view['controls'].append('Shop');view['shop_preparation']=asset['editor_report'];observed['shop_preparation_candidate']=asset['candidate']
(spec/'presentation-observation.v15.json').write_text(json.dumps(observed,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
unit=next(u for u in current['units'] if u['id']=='TEST-APPEAR')
note=unit['owns'][0].removesuffix('.cs')+'.repair-v15.md';unit['owns'] += [note,note+'.meta']
guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
finding=json.loads((run/'dossier-v14.json').read_bytes())['failed_units'][0]['hypothesis']
unit['instructions']='Repair the 23 mapped L3/L7/Journey_ECON tests in the existing partial class, preserving every effective assertion and the other partial file. Latest independent findings: '+finding+' The dedicated Shop binding is now actually prepared; use action Shop and the contextual menu independently. Apply the already approved handoff-scope disposition in approved-rehearsal-scope.v15.md; actual in-match locomotion is not part of this lobby rehearsal. Independently reviewed presentation observation helpers are supplied as read-only reference mechanics, not callable public private-method APIs. Safely await entry/cleanup. This host uses strict hash-bound edit transport for owned C# repairs, leaving every other source byte intact; obey its schema rather than historical full-file output hints. Update LobbyEconomyTests.acceptance.md with clause-level evidence and explicit disposition. Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Preserve all historical notes, public APIs, partial class identity and every test ID. Tests are not globally frozen; never implement game business behavior.'
next(u for u in current['units'] if u['id']=='SHELL')['instructions']+=' The verified Lobby prefab now exposes dedicated Shop action beside the wallet; wire it to default-skins Shop independently of the contextual-menu entry. Preserve approved-rehearsal-scope.v15.md and original source dispositions.'
def ref(path):return {'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
profile['rules'].append(ref(scope_path))
profile['protected_paths']=list(dict.fromkeys(profile['protected_paths']+asset_paths[1:]+[scope_path,'specs/monopoly-game-lobby/acceptance-conditions.v15.json','specs/monopoly-game-lobby/presentation-observation.v15.json']))
(spec/'coding-profile.v15.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='');current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v15.json')
presentation=json.loads((source/old['presentation_ref']['path']).read_bytes())
presentation['files']=[ref(row['path']) if row['path']==lobby else row for row in presentation['files']]
known={row['path'] for row in presentation['files']}
presentation['files'] += [ref(path) for path in asset_paths[1:] if path not in known]
(spec/'presentation.v15.json').write_text(json.dumps(presentation,ensure_ascii=False,indent=2),encoding='utf-8',newline='');current['presentation_ref']=ref('specs/monopoly-game-lobby/presentation.v15.json')
for name in ('proposal.md','design.md'):(spec/name).write_bytes((directory/name).read_bytes())
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
(spec/'planning-context.v15.json').write_text(json.dumps(context.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8',newline='')
(spec/'contract.v15.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter();contracts=[]
for n in range(1,16):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=30))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
git(source,'add','specs/monopoly-game-lobby',*asset_paths)
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Reconcile verified Shop binding and approved handoff scope for delegated repair')
policy=json.loads((state/'budget-policy.json').read_bytes());budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
def reconciled():
    for call_id,call in json.loads((run/'budget.json').read_bytes())['calls'].items():
        if 'actual' in call:continue
        if call_id!='v8-step3-prepare-review-TEST-PRES-CORE':return False
        retained_transport_failure(json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()),call,8)
    return json.loads((run/'services-v14/effects/transaction.json').read_bytes()).get('complete') is True and not git(source,'status','--porcelain')
lease=RunLease(state,'monopoly-game-lobby','cycle15-transition-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
try:
    transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
    active={'version':15,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v15','contract_sha256':contracts[-1].sha256}
    atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
    print(json.dumps(active|{'preserved_usage':budget.totals(),'limits':budget.limits,'test_ids':len(current['test_links']),'game_behavior_written':False}))
finally:lease.release()
