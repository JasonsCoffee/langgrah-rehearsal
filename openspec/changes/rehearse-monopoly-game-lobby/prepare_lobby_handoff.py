"""Export the selected planning store and prepare the isolated runtime handoff."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.presentation import Presentation
from unity_coder.adapters.unity import UnityAdapter

framework = Path.cwd().resolve()
change = framework / 'openspec/changes/rehearse-monopoly-game-lobby'
run = Path(os.environ['LOBBY_RUN_ROOT']).resolve()
module = run / 'module'
game = Path(os.environ['UNITY_HOST']).resolve() / 'Assets/JJGame/monopoly'
spec = module / 'specs/monopoly-game-lobby'
if (spec/'contract.v1.json').exists():
    raise ValueError('This handoff is frozen; use the documented contract transition rather than rerunning preparation')
spec.mkdir(parents=True,exist_ok=True)
rules = UnityAdapter()

def write(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data.encode('utf-8') if isinstance(data,str) else data)

def emit(path, data):
    write(path,json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def ref(path):
    return {'path':path.relative_to(module).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest()}

sources = {}
names = ('大赢家主界面策划案.docx','大赢家局外主界面-需求分析.md','大赢家局外主界面-用户故事.md')
for index,name in enumerate(names):
    source = game / 'Docs~/Design/Lobby' / name
    # Word may hold the original open; the previously inspected identical copy
    # is accepted only against its already recorded original identity.
    if index == 0:
        source = Path(os.environ['LOBBY_DOCX_COPY'])
        if sha256(source.read_bytes()).hexdigest() != '0ea481c3a41678c896cc5dd3c05c90bedc92d384bf536eb4be76d021e5f6da0e':
            raise ValueError('Original design copy changed')
    target = change / 'sources' / name
    write(target,source.read_bytes())
    sources['original-'+str(index)] = target.relative_to(framework).as_posix()
    write(spec / 'sources' / name,target.read_bytes())
for name in ('proposal.md','design.md','brainstorm.md'):
    write(spec/name,(change/name).read_bytes())
with ZipFile(change/'sources'/names[0]) as archive:
    document = ET.fromstring(archive.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs=[''.join(p.itertext()) for p in []]  # Text nodes only, preserve paragraph order.
    paragraphs=[''.join(p.itertext()) for p in document.findall('.//w:t',ns)]
    write(spec/'sources/design-text.txt','\n'.join(paragraphs))
raw = subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
instructions=json.loads(raw)
write(framework/'.agent/lobby-apply.json',raw)
emit(framework/'.agent/lobby-sources.json',sources)
context=discover_context(framework,instructions,sources=sources)
emit(spec/'planning-context.json',context.to_dict())
write(spec/'spec.md',(change/'specs/monopoly-game-lobby/spec.md').read_bytes())
write(spec/'presentation-observation.json',(run/'trusted-state/presentation/presentation-preparation.json').read_bytes())
builder=(change/'LobbyPreparation.cs').read_text(encoding='utf-8')
write(spec/'presentation-context.md','Prepared catalog data and action names (Architect construction, not delegated business behavior):\n```csharp\n'+builder[builder.index('            for (var i = 0; i < 6;'):builder.index('            for (var i = 0; i < 6;')+3500]+'\n```\n') if '            for (var i = 0; i < 6;' in builder else write(spec/'presentation-context.md',builder)

design=(change/'design.md').read_text(encoding='utf-8')
rows=re.findall(r'^\| (US-[^| ]+) \| ([^|]+) \| ([^|]+) \| ([A-Za-z]+Tests)\.(Story_[^| ]+) \|',design,re.M)
if len(rows)!=119:
    raise ValueError('Story mapping is incomplete')
suite_units={'LobbyPresentationTests':'SHELL','LobbyEconomyTests':'ECON','LobbyMatchTests':'MATCH','LobbySocialTests':'SOCIAL','LobbyRecordsSettingsTests':'RECORDS'}
namespace='jj.Monopoly.Tests.LobbyRehearsal.'
testlinks=[]
test_units=[]
testroot='Tests/Runtime/Script/LobbyRehearsal/'
for suite,impl in suite_units.items():
    acceptance=[namespace+suite+'.'+r[4] for r in rows if r[3]==suite]
    extra='Journey_'+impl
    acceptance.append(namespace+suite+'.'+extra)
    author='TEST-'+impl
    path=testroot+suite+'.cs'
    # Prepare metadata before authoring; first materialization occurs only after
    # the graph has created the corresponding owned test source files.
    guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/tests/'+path).hex
    write(module/(path+'.meta'),'fileFormatVersion: 2\nguid: '+guid+'\n')
    test_units.append(dict(id=author,role='test',status='active',title=suite,spec_ref='LOBBY',owns=[path],acceptance=acceptance,depends_on=[],interfaces=[],instructions=
        'Author concrete NUnit EditMode tests for every exact mapped method and the extra '+extra+' integration journey. Namespace jj.Monopoly.Tests.LobbyRehearsal. Each story method must cover the source acceptance clauses as overridden by the approved proposal. Do not merely assert fixture state, source strings, non-null or expected stubs. Exercise real service/public UI coordinator methods and outcomes, include negative and race cases. All tests must compile against the frozen APIs; do not invent API members. Put independent helpers inside your owned file with unique names. Use an in-memory ILobbyPersistence test double; ScriptableObject.CreateInstance<LobbyConfiguration> and load the prepared catalog asset with AssetDatabase.LoadAssetAtPath when needed. Arrange peer DTOs directly in world.State to avoid setup errors in the nonfunctional baseline; assert behavior rather than throw from setup. Do not instantiate VVMP view models without the framework Injector. Await completed UniTasks via GetAwaiter().GetResult only for the pure fake UI port. Inspect prepared prefab bindings with AssetDatabase, no real network or unrelated game tests. Tests may not modify assets, global clock, shared fonts, settings or other files. Include an ILobbyUiPort recording fake for coordinator behavior. Test methods must be nonparameterized [Test], no skips, no disabled tests. Source exclusion stories assert the exclusion. The baseline intentionally has no business behavior.'))
    for test in acceptance:
        implementers=[impl]
        if impl != 'SHELL':
            implementers.append('SHELL')
        if test.endswith('.'+extra):
            implementers=list(suite_units.values())
        testlinks.append(dict(test_id=test,author_unit=author,implementing_units=implementers,criterion='LOBBY'))
foldermeta=module/(testroot.rstrip('/')+'.meta')
write(foldermeta,'fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/tests/folder').hex+'\nfolderAsset: yes\n')
emit(spec/'story-test-map.json',[dict(story=r[0],title=r[1].strip(),functional_ids=r[2].strip(),test=namespace+r[3]+'.'+r[4]) for r in rows])

ui='Runtime/Script/UI/LobbyRehearsal/'
owned={
 'SHELL':['Runtime/Script/Monopoly.cs',ui+'Monopoly.LobbyRehearsal.cs',ui+'LobbyShellBindings.cs',ui+'LobbyRehearsalPanel.cs'],
 'ECON':[ui+'LobbyEconomy.cs'],'MATCH':[ui+'LobbyMatch.cs'],'SOCIAL':[ui+'LobbySocial.cs'],'RECORDS':[ui+'LobbyRecordsSettings.cs']}
descriptions={
 'SHELL':'Implement the actual existing Game/Scene entry, paired Root lifecycle and all ten VVMP screens, every prepared action and row interaction, responsive safe areas and variable chat rows, real 3D preview/camera integration, 6 skins/4 vehicles, animation action changes, seat anchor, fake platform home and re-entry. Implement partial VM lifecycle and presenter back hooks in owned LobbyShellBindings.cs. Use a nested concrete ILobbyUiPort and IUserDefault persistence adapter in the existing-entry partial extension. Implement Editor panel account/peer/clock controls against the active owned instance; do not create static runtime business state. Expose instance LobbyShellBindings for Editor inspection through an instance public property on Monopoly. Clone fonts, materials and atlas textures in memory for runtime glyph changes; never persist shared TMP assets or mutate protected serialized files. Honor shop reopen sorting, preserved drafts, confirmations and tabs. All original existing entry methods must route coherently and cleanup on Leave/Exit/OnDestroy. Use the existing Root Navigator, resource loader and camera stack; do not create duplicate EventSystem/audio listener/base camera. Preserve the protected original Root scene. No placeholder TODO handlers or hidden inaccessible features.',
 'ECON':'Implement fake clock, account-isolated IUserDefault-bound persistence through ILobbyPersistence, approved balances, appearance ownership/equip/expiry/defaults, all wallet/recharge/exchange and partial checkout outcomes, one-time retry-safe transactions, card periodic catch-up/extension and platform VIP. Configuration is authoritative. Account queries must not create unknown accounts; EnsureAccount creates explicitly. Initialize may restore durable state but must not overwrite another account. All fake clock advancement processes due rewards and delegates Match.Tick and Social.Tick. Operations are idempotent and reject reused keys with different intent. Never silently use wall time in fake services. Use the project JSON library for typed durable state; no PlayerPrefs. Include persistence schema version and validation.',
 'MATCH':'Implement fake two-person parties, exact invite races/expiry/full feedback, tier synchronization, atomic balance validation and fees only at match start, heartbeat/timeout bot fill to 24, deterministic faction assignment keeping party peers together, cancellation, preserved AI-controlled disconnected seats/reconnect, handoff, confirmation abandonment/no rejoin and deterministic one-time completed settlement. Publish typed record data through RecordsSettings and preserve accounting semantics. Lock world.Sync for atomic transitions; do not rely on UI button disable for correctness.',
 'SOCIAL':'Implement fake platform friend lookup/request/expiry/cap/accept/reject/remove and conversations, world/private chat permissions, Unicode scalar limit200/cooldown3/preserved UI draft via failure feedback, delivery/read/visible-channel semantics, latest successfully delivered world marquee and independent unread counters, long-press confirmed moderation recording. All peers use the same synthetic ID. Lock world.Sync and coordinate shared clock. Failed sends must not create records/unreads or consume successful send cooldown.',
 'RECORDS':'Implement fake result publication/history/pagination/details/accounting, rolling 24h/7day shared-timestamp top100 ranking (UI ten rows plus pinned self), deterministic ties, recent qualifying partner/opponent recommendations bounded20 each, persisted per-account audio/quality overrides, device initial quality, support/rules/about. Use UTC fake timestamps and Asia/Shanghai calendar. Never derive abandoned rank as numeric completed rank; the UI must display 已放弃. Ranking snapshots must use one captured fake time.'}
impl_units=[]
for unit,paths in owned.items():
    cls={'ECON':'LobbyEconomy','MATCH':'LobbyMatch','SOCIAL':'LobbySocial','RECORDS':'LobbyRecordsSettings'}.get(unit)
    interfaces=[] if cls is None else [dict(symbol='jj.Reserve04.Runtime.LobbyRehearsal.'+cls,signature='class '+cls)]
    impl_units.append(dict(id=unit,role='impl',status='active',title=unit+' lobby implementation',spec_ref='LOBBY',owns=paths,
        acceptance=[t['test_id'] for t in testlinks if unit in t['implementing_units']],depends_on=[],interfaces=interfaces,instructions=descriptions[unit]))

tracked=subprocess.check_output(['git','-C',str(module),'ls-files','-z']).decode().split('\0')
protected=[p for p in tracked if p and p not in {p for paths in owned.values() for p in paths}]
protected += [testroot.rstrip('/')+'.meta']+[testroot+s+'.cs.meta' for s in suite_units]
presentationpaths=[p for p in protected if p.startswith('Runtime/Resource/') or p.startswith(ui) and p.endswith(('.cs','.meta'))]
entries=['Runtime/Resource/monopoly/Scenes/LobbyRehearsal/LobbyStreet_placeHolder.unity','Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/LobbyView_placeHolder.prefab']
manifest=dict(revision=subprocess.check_output(['git','-C',str(module),'rev-parse','HEAD']).decode().strip(),files=[ref(module/p) for p in presentationpaths],interfaces=[],entries=entries,mutations=[],assets=[],reused=[],instructions=
    'Use the existing Monopoly Game/Scene entry in Play Mode. Review the 3D street, character, vehicle, five tiers and wallet. Open all menu pages; test Chat and Invite teammate shortcuts, appearance switching and Idle/Wave/Celebrate. Use the Editor rehearsal panel to switch synthetic accounts, advance the fake clock and send peer actions. Exercise recharge/exchange/cards, invitation races, full-party matching, 30-second bot fill, disconnect/reconnect, abandon and completed settlement, ranking/history and account restart persistence. Return to platform home and re-enter. Inspect portrait ratios 9:16, 1:2 and 9:19.5. Original geometry is placeholder art; all workflows must be functional. Runtime bindings may change labels, visibility, row content/heights, scroll offsets, previews, safe areas and animations in memory only; saved layout and asset identities remain frozen.')
emit(spec/'presentation.json',manifest)
Presentation(manifest['revision'],tuple(__import__('unity_coder.core.contracts',fromlist=['ArtifactRef']).ArtifactRef(**r) for r in manifest['files']),(),tuple(entries),(),(),(),manifest['instructions']).validate(module)
profile=dict(format_version=1,host_selector='UNITY_HOST',game_selector='LOBBY_MODULE',allowed_mount='Assets/JJGame/monopoly',implementation_roots=['Runtime/Script'],test_roots=[testroot.rstrip('/')],rules=[ref(module/'AGENTS.md')],sources=[dict(source_id='original-'+str(i),**ref(spec/'sources'/name)) for i,name in enumerate(names)],protected_paths=protected)
# Shared signatures and prepared bindings are explicit coding context.
profile['rules'] += [ref(module/p) for p in protected if p.startswith(ui) and p.endswith('.cs')]
context_paths = [
    'Assets/JJGame/monopoly/Runtime/Script/MonopolyRootScene.cs',
    'Assets/JJWidget/widgetsdk/Runtime/Script/UIFramework/Base/ViewModel.cs',
    'Assets/JJWidget/widgetsdk/Runtime/Script/UIFramework/Base/Presenter.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/WidgetSDK/INavigator.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/IUserDefault.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/IGlobalSchedule.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IDeviceRatingService.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IQualityMatchingService.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IQualityModifyService.cs',
    'Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/TKGameService/Sound/ISoundService.Public.cs',
]
context_text=[]
for relative in context_paths:
    data=(game.parents[2]/relative).read_bytes()
    context_text.append('## '+relative+'\nSHA256 '+sha256(data).hexdigest()+'\n```csharp\n'+data.decode('utf-8-sig')+'\n```\n')
write(spec/'framework-context.md','\n'.join(context_text))
profile['rules'].append(ref(spec/'framework-context.md'))
emit(spec/'coding-profile.json',profile)
emit(spec/'environment.json',dict(format_version=1,engine='Tuanjie',project_version=(Path(os.environ['UNITY_HOST'])/'ProjectSettings/ProjectVersion.txt').read_text(),host_selector='UNITY_HOST',mount='Assets/JJGame/monopoly',bridge_protocol=1,verification='sequential isolated EditMode selection',baseline_sha256='12f3b9e07d8085e8ad0558e02223988c7313ac4392f77d9c80a91d8c6e6d74a0'))
tasklinks=[dict(task_ref='rehearse-monopoly-game-lobby:'+str(task['id']),unit_ids=[u['id'] for u in test_units+impl_units],criteria=['LOBBY']) for task in instructions['tasks'] if str(task['id']) in ('9','16','17','18','19','20','21','23','26')]
contract=dict(format_version=1,contract_version=1,module='monopoly-game-lobby',module_root='.',test_roots=[testroot.rstrip('/')],spec_ref='specs/monopoly-game-lobby/spec.md',spec_sha256=sha256((spec/'spec.md').read_bytes()).hexdigest(),presentation_ref=ref(spec/'presentation.json'),coding_profile_ref=ref(spec/'coding-profile.json'),environment_ref=ref(spec/'environment.json'),task_links=tasklinks,test_links=testlinks,ownership_migrations=[],units=test_units+impl_units)
# One implementation scope contains the entry and client code. The Editor-only
# review panel lives under this scope with an explicit UNITY_EDITOR guard.
contract['module_root']='Runtime'
panel=module/(ui+'LobbyRehearsalPanel.cs')
if not panel.exists():
    write(panel,'// Nonfunctional review-panel shell, owned by SHELL.\n#if UNITY_EDITOR\nusing UnityEditor;\nnamespace jj.Reserve04.Runtime.LobbyRehearsal\n{\n    public sealed class LobbyRehearsalPanel : EditorWindow { }\n}\n#endif\n')
    write(Path(str(panel)+'.meta'),'fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/runtime-panel').hex+'\n')
emit(spec/'contract.draft.json',contract)
emit(run/'trusted-state/handoff-draft.json',dict(stories=len(rows),tests=len(testlinks),units=len(test_units+impl_units),context=context.to_dict(),execution_contract_frozen=False))
print('Exported portable source provenance, story/test mappings and draft contract')
