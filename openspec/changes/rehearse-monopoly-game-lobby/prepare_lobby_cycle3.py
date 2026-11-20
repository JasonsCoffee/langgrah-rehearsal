"""Prepare the last bounded cycle with a separately delegated test harness."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import NAMESPACE_URL,uuid5
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git

framework=Path.cwd().resolve()
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
module=root/'module'
source=root/'worktrees/architect-v3'
if source.exists():
    if (os.environ.get('LOBBY_RECONCILE_CYCLE3_PREP')!='1'
        or git(source,'rev-parse','HEAD').decode().strip()!='6b3b560cfa856c84627c159b226d3ce5978e2250'
        or (source/'specs/monopoly-game-lobby/contract.v3.json').exists()):
        raise ValueError('Architect cycle-3 workspace exists; no implicit replay')
else:
    git(module,'worktree','add','-b','codex/lobby-architect-v3',str(source),'6b3b560cfa856c84627c159b226d3ce5978e2250')
spec=source/'specs/monopoly-game-lobby'
testroot='Tests/Runtime/Script/LobbyRehearsal/'
old=json.loads((spec/'contract.v2.json').read_bytes())
for unit in old['units']:
    if unit['role']!='test':continue
    # Rejected, never-frozen artifacts remain in cycle-2 history. They have not
    # been materialized in Unity; omit them here to force fresh native authorship.
    for artifact in unit['owns'][1:]:
        if (source/artifact).exists():
            git(source,'rm','--',artifact)
    original=git(source,'show','faeb848d975e1bb96a7788f710420e4b40809397:'+unit['owns'][0])
    (source/unit['owns'][0]).write_bytes(original)

harness='''// Architect-prepared test-scaffolding API. All bodies are delegated.
using System;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using jj.Reserve04.Runtime.LobbyRehearsal;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace jj.Monopoly.Tests.LobbyRehearsal
{
    public static class LobbyHarness
    {
        public static LobbyConfiguration Configuration() { return null; }
        public static LobbyWorld World(LobbyMemoryStore store = null, bool seed = true) { return null; }
        public static LobbyStreetBinding OpenStreet(out Scene preview) { preview = default; return null; }
        public static void CloseStreet(Scene preview) { }
        public static LobbyRehearsalViewBase View(string screen, Transform parent = null) { return null; }
        public static LobbyControlBinding Control(LobbyRehearsalViewBase view, string action) { return null; }
        public static void DestroyConfiguration(LobbyConfiguration configuration) { }
    }
    public sealed class LobbyMemoryStore : ILobbyPersistence
    {
        public readonly Dictionary<string,string> Data = new Dictionary<string,string>();
        public readonly List<string> Reads = new List<string>();
        public readonly List<string> Writes = new List<string>();
        public int Flushes;
        public string Read(string key) { return ""; }
        public void Write(string key, string value) { }
        public void Flush() { }
    }
    public sealed class LobbyRecordingUiPort : ILobbyUiPort, IDisposable
    {
        public string LastScreen = "";
        public string LastTab = "";
        public string LastPeer = "";
        public string ClipboardText = "";
        public readonly List<string> Routes = new List<string>();
        public readonly List<string> Notices = new List<string>();
        public bool LastMusic;
        public bool LastEffects;
        public int LastQuality = -1;
        public LobbyRehearsalViewBase CurrentView { get; private set; }
        public RectTransform CanvasRoot { get; private set; }
        public string Version => "lobby-test";
        public int DeviceQualityTier => 1;
        public int LowestQualityTier => 0;
        public int HighestQualityTier => 3;
        public UniTask NavigateAsync(string screen, LobbyShellBindings context) { return UniTask.CompletedTask; }
        public UniTask BackAsync() { return UniTask.CompletedTask; }
        public void Notify(string message) { }
        public void Copy(string value) { }
        public string Paste() { return ""; }
        public void ApplyAudio(bool music, bool effects) { }
        public void ApplyQuality(int tier) { }
        public void Dispose() { }
    }
    public sealed class LobbyRecordingEntryPort : ILobbyEntryPort, IDisposable
    {
        public int RootEnters;
        public int RootLeaves;
        public int StreetLoads;
        public int StreetUnloads;
        public LobbyStreetBinding CurrentStreet { get; private set; }
        public UniTask EnterRootAsync() { return UniTask.CompletedTask; }
        public UniTask LeaveRootAsync() { return UniTask.CompletedTask; }
        public UniTask<LobbyStreetBinding> LoadStreetAsync() { return UniTask.FromResult<LobbyStreetBinding>(null); }
        public UniTask UnloadStreetAsync() { return UniTask.CompletedTask; }
        public void Dispose() { }
    }
    public sealed class LobbyHarnessTests { }
}
'''
path=testroot+'LobbyHarness.cs'
(source/path).write_text(harness,encoding='utf-8',newline='')
guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/harness-v3').hex
(source/(path+'.meta')).write_text('fileFormatVersion: 2\nguid: '+guid+'\n',encoding='utf-8',newline='')
(spec/'test-harness-api.v3.txt').write_text(harness,encoding='utf-8',newline='')
checklist=testroot+'LobbyHarness.acceptance.md'
checkguid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/harness-v3-checklist').hex
testid='jj.Monopoly.Tests.LobbyRehearsal.LobbyHarnessTests.PreparedAssetsAreInspectable'
unit=dict(id='TEST-HARNESS',role='test',status='active',title='Shared real-asset Editor test scaffolding',spec_ref='LOBBY',
    owns=[path,checklist,checklist+'.meta'],acceptance=[testid],depends_on=[],
    interfaces=[{'symbol':'jj.Monopoly.Tests.LobbyRehearsal.LobbyHarness','signature':'class LobbyHarness'}],
    add_justification='Two real preparation dossiers showed invalid duplicated scene loaders and fake adapters; isolate and independently review the shared scaffolding before consumer tests.',
    instructions='Implement only the prepared test harness API and the single mapped readiness test. Do not implement or fake any game business behavior. Load the actual configuration from Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/Art/LobbyConfiguration_placeHolder.asset and clone it. Open the .unity street with EditorSceneManager.OpenPreviewScene, get the actual LobbyStreetBinding from scene roots, and close using ClosePreviewScene. Never load a .unity as GameObject. View loads/instantiates the ten prepared prefab assets under an inactive temporary Canvas parent, never mutates original assets and never saves assets. Control finds the actual serialized control by exact Action. World creates LobbyWorld and optionally directly seeds three DTO accounts acc-A, acc-B, acc-C (male/female/any) with configured starting balances and eligible default grants for fixture arrangement; seed=false must not overwrite persisted state. MemoryStore is an ordinary dictionary plus observation logs. RecordingUiPort must record the actual supplied screen and context.Tab/SelectedPeerId, instantiate/bind the real view, maintain a visual view stack and rebind the previous view on Back; never write expected coordinator Screen/Tab/selection or any world business state. Copy/Paste, settings and notifications only record supplied data. RecordingEntryPort loads/closes the actual preview scene, records actual method invocation counts, and never creates a fake LobbyStreetBinding. Dispose only owned temporary objects/previews. All fake-port UniTasks complete synchronously. The single NUnit [Test] PreparedAssetsAreInspectable must prove the real catalog, scene, geometry/animation references and ten prefab/control bindings can be loaded, that storage logs reflect actual operations, and that adapters observe calls without manufacturing business state. Other source stories belong to consumer suites. Preserve every prepared public signature. Write all three owned files, including an accurate readiness checklist and metadata exactly fileFormatVersion: 2 newline guid: '+checkguid+' newline.')
current=old|{'contract_version':3,'previous_contract_sha256':sha256((spec/'contract.v2.json').read_bytes()).hexdigest()}
current['units']=[unit]+current['units']
for item in current['units'][1:]:
    if item['role']=='test':
        item['depends_on']=['TEST-HARNESS']
        item['instructions']+=' Cycle 3: use the independently reviewed LobbyHarness, LobbyMemoryStore, LobbyRecordingUiPort and LobbyRecordingEntryPort instead of duplicating broken scene loaders or fake UI behavior. Their API is in test-harness-api.v3.txt and their actual implementation is supplied. Do not change that file. No vacuous >=0, object-is-present-only, self-comparison, do-nothing simulation or direct expected-state assignment can count as behavior. Every applicable acceptance clause needs nonempty stimuli and exact observable outcomes. Test only this unit\'s mapped clauses; other suites cover their own stories. Read and repair every explicit judge finding before returning a patch.'
    if item['id']=='SHELL':item['acceptance'].append(testid)
current['test_links'].append(dict(test_id=testid,author_unit='TEST-HARNESS',implementing_units=['SHELL'],criterion='LOBBY'))
for link in current['task_links']:
    link['unit_ids'].insert(0,'TEST-HARNESS')
runtime=(spec/'spec.md').read_text(encoding='utf-8')+'''\n### Requirement: Test harness preparation

The shared test harness SHALL load actual prepared scene, prefab and configuration assets, provide observation-only adapters and in-memory persistence, release all temporary objects, and leave source assets unchanged. It SHALL NOT implement game business behavior. Its readiness test covers this preparation requirement; the 119 source stories remain assigned to consumer suites.

#### Scenario: Real fixtures and faithful observation

- **WHEN** the readiness test opens the prepared street as a preview scene, loads the catalog and instantiates each prepared view
- **THEN** it inspects the real geometry, animation references and serialized controls
- **AND** adapter observations reflect actual calls without setting expected coordinator or domain state
- **AND** all temporary previews, views and cloned configurations are released without saving source assets
'''
(spec/'spec.v3.md').write_text(runtime,encoding='utf-8',newline='')
current['spec_ref']='specs/monopoly-game-lobby/spec.v3.md'
current['spec_sha256']=sha256((spec/'spec.v3.md').read_bytes()).hexdigest()
profile=json.loads((spec/'coding-profile.v2.json').read_bytes())
profile['protected_paths'] += [path+'.meta','specs/monopoly-game-lobby/test-harness-api.v3.txt']
(spec/'coding-profile.v3.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
current['coding_profile_ref']={'path':'specs/monopoly-game-lobby/coding-profile.v3.json','sha256':sha256((spec/'coding-profile.v3.json').read_bytes()).hexdigest()}
(spec/'contract.v3.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
(spec/'planning-context.v3.json').write_text(json.dumps(context.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
rules=UnityAdapter(); previous=None
for version in (1,2,3):previous=load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,previous=previous)
policy=load_profile((spec/'coding-profile.v3.json').read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',))
policy.validate_contract(previous)
git(source,'add','.')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare cycle 3 independently delegated real-asset test harness')
print('VALID cycle3',previous.sha256,'units',len(previous.units),'selected tests',len(previous.test_links))
