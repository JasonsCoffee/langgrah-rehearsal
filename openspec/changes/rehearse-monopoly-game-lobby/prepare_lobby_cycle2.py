"""Architect-only cycle-2 testability signatures and versioned handoff."""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile
from unity_coder.adapters.unity import UnityAdapter

framework=Path.cwd().resolve()
change=Path(__file__).parent
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
module=root/'module'
target=root/'worktrees/architect-v2'
if target.exists():
    raise ValueError('Cycle-2 Architect workspace already exists; reconcile instead of replaying')
base='1432d3765474c5cf5a0f390eab26ddfa5fe5a94e'
subprocess.check_call(['git','-C',str(module),'worktree','add','-b','codex/lobby-architect-v2',str(target),base])
spec=target/'specs/monopoly-game-lobby'
ui=target/'Runtime/Script/UI/LobbyRehearsal'
def write(path,text):
    path.write_bytes(text.encode('utf-8'))
def emit(path,data):
    write(path,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def ref(path):
    return {'path':path.relative_to(target).as_posix(),'sha256':sha256(path.read_bytes()).hexdigest()}
port=(ui/'LobbyUiPort.cs').read_text(encoding='utf-8')
port=port.replace('    public interface ILobbyUiPort','''    public interface ILobbyEntryPort
    {
        UniTask EnterRootAsync();
        UniTask LeaveRootAsync();
        UniTask<LobbyStreetBinding> LoadStreetAsync();
        UniTask UnloadStreetAsync();
    }

    public interface ILobbyUiPort''')
write(ui/'LobbyUiPort.cs',port)
shell=(ui/'LobbyShellBindings.cs').read_text(encoding='utf-8').replace('using Cysharp.Threading.Tasks;','using Cysharp.Threading.Tasks;\nusing UnityEngine;')
shell=shell.replace('        public LobbyWorld World => world;','''        public LobbyWorld World => world;
        public ILobbyEntryPort EntryPort { get; set; }
        public int BoundViewCount => 0;

        public void BindView(LobbyRehearsalViewBase view) { }
        public void UnbindView(LobbyRehearsalViewBase view) { }
        public void BindStreet(LobbyStreetBinding street) { }
        public void ConfigureViewport(int width, int height, Rect safeArea) { }
        public UniTask ShutdownAsync() { return UniTask.CompletedTask; }
''')
write(ui/'LobbyShellBindings.cs',shell)
entry=ui/'Monopoly.LobbyRehearsal.cs'
write(entry,'''// Architect-prepared existing-entry injection signature; behavior is delegated.
namespace jj.Reserve04.Runtime
{
    public partial class Monopoly
    {
        public void ConfigureLobbyRehearsal(LobbyRehearsal.LobbyShellBindings shell, string accountId)
        {
        }
    }
}
''')
write(spec/'design.v2.md',(change/'design.md').read_text(encoding='utf-8'))
technical=(change/'design.md').read_text(encoding='utf-8').split('### Cycle 2:')[1].split('### Source authority')[0]
write(spec/'binding-protocol.v2.md','# Cycle-2 client binding protocol\n'+technical)
source=(spec/'sources/大赢家局外主界面-用户故事.md').read_text(encoding='utf-8-sig')
mapping=json.loads((spec/'story-test-map.json').read_bytes())
conditions=[]
for row in mapping:
    match=re.search(r'^### '+re.escape(row['story'])+r'[:：].*?(?=^### US-|^## |\Z)',source,re.M|re.S)
    if match is None: raise ValueError('Missing original story '+row['story'])
    block=match.group(0)
    conditions.append(row|{'source_story':block,'required_check':'Map every acceptance clause to observable assertions in the named test; binding/lifecycle adapters may be injected, prepared assets and runtime instance state must be real.'})
emit(spec/'acceptance-conditions.v2.json',conditions)
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
emit(spec/'planning-context.v2.json',context.to_dict())
old=json.loads((spec/'contract.v1.json').read_bytes())
profile=json.loads((spec/'coding-profile.json').read_bytes())
profile['rules']=[ref(target/r['path']) for r in profile['rules']]
profile['rules'].append(ref(spec/'binding-protocol.v2.md'))
profile['protected_paths'] += ['specs/monopoly-game-lobby/binding-protocol.v2.md','specs/monopoly-game-lobby/acceptance-conditions.v2.json']
emit(spec/'coding-profile.v2.json',profile)
presentation=json.loads((spec/'presentation.json').read_bytes())
presentation['revision']='cycle-2-observable-bindings'
presentation['files']=[ref(target/r['path']) for r in presentation['files']]
emit(spec/'presentation.v2.json',presentation)
current=old|{'contract_version':2,'previous_contract_sha256':sha256((spec/'contract.v1.json').read_bytes()).hexdigest(),
    'coding_profile_ref':ref(spec/'coding-profile.v2.json'),'presentation_ref':ref(spec/'presentation.v2.json')}
for unit in current['units']:
    unit['instructions']+=' Cycle 2: use binding-protocol.v2.md and acceptance-conditions.v2.json. Every source acceptance clause must have observable assertions and a matching comment; exact prepared asset inventory is authoritative. No invented button aliases. Preserve all frozen signatures.'
    if unit['role']=='test':
        unit['instructions']+=' The exact configuration asset is Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/Art/LobbyConfiguration_placeHolder.asset. Bind real inactive prefab instances through BindView (no Injector needed), bind a preview-scene LobbyStreetBinding through BindStreet, and inject a recording ILobbyEntryPort. Test ConfigureViewport with all three aspect ratios and clipped safe areas. Use the actual Monopoly instance via FormatterServices.GetUninitializedObject, ConfigureLobbyRehearsal(shell,id), EnterAsync(null,null), ResumeAsync(null,null,null), LeaveAsync and ExitAsync to assert paired port calls without SDK initialization. Do not mutate original assets; use inactive parents, private in-memory font/material/atlas clones and clean all instances/previews. Source strings and nonnegative counters cannot replace rendered-state assertions. For UI breadth assert control effects and preserved caller/selection/scroll, exact route/presenter/view-model pairings, badges, draft retention and account-separated durable state. Keep pure-domain methods free of irrelevant UI setup.'
    if unit['id']=='SHELL':
        unit['instructions']+=' Implement the prepared BindView/BindStreet/ConfigureViewport/lifecycle hooks in the owned coordinator, and ConfigureLobbyRehearsal in the owned Monopoly partial. The same hooks must be used by the production VVMP adapter. Tests inject only ports, not fake business logic. Actual existing Enter/Resume/Launch and Leave/Exit/Destroy must route this instance-owned rehearsal. Shell Exit navigates simulated platform home; Shutdown releases complete lifecycle. Avoid live match/protocol operations in the rehearsal path.'
emit(spec/'contract.v2.json',current)
rules=UnityAdapter()
previous=load_contract((spec/'contract.v1.json').read_bytes(),target,rules)
contract=load_contract((spec/'contract.v2.json').read_bytes(),target,rules,previous=previous)
policy=load_profile((spec/'coding-profile.v2.json').read_bytes(),target,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',))
policy.validate_contract(contract)
subprocess.check_call(['git','-C',str(target),'add','.'])
subprocess.check_call(['git','-C',str(target),'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare cycle 2 observable lobby binding and lifecycle contract'])
print('VALID cycle2',contract.sha256)
