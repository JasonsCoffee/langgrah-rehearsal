"""Freeze repaired presentation and consecutive contract, then native rework transition."""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
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


def main() -> None:
    framework=Path.cwd().resolve()
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    source=root/'worktrees/architect-v5'
    state=root/'trusted-state'
    spec=source/'specs/monopoly-game-lobby'
    if (spec/'contract.v5.json').exists():raise ValueError('Prepared contract exists; reconcile instead of rewriting')
    completed=json.loads((state/'presentation-repair-v5/complete.json').read_bytes())
    if git(source,'rev-parse','HEAD').decode().strip()!=completed['candidate']:
        raise ValueError('Presentation repair candidate changed')
    def ref(relative):return {'path':relative,'sha256':sha256((source/relative).read_bytes()).hexdigest()}
    guide='specs/monopoly-game-lobby/test-preparation-guidance.v5.md'
    (source/guide).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby/test-preparation-guidance.v5.md').read_bytes())
    old=json.loads((spec/'contract.v4.json').read_bytes())
    current=old|{'contract_version':5,'previous_contract_sha256':sha256((spec/'contract.v4.json').read_bytes()).hexdigest()}
    for unit in current['units']:
        if unit['role']=='test':
            unit['instructions']=unit['instructions'].replace('EditorSceneManager.OpenPreviewScene','EditorSceneManager.OpenScene(path, OpenSceneMode.Additive)').replace('ClosePreviewScene','CloseScene(scene, true)')
            unit['instructions']+=' Version 5 supersedes prior fixture assumptions: follow test-preparation-guidance.v5.md and test-harness-api.v5.txt, verified target API and new serialized bindings. Never use OpenPreviewScene. Prior tests were rejected and never frozen; fresh meaningful tests must satisfy every applicable mapped source clause. Preserve actual public APIs and write truthful coverage maps. '
            if unit['id'] in ('TEST-HARNESS','TEST-SHELL'):
                note=unit['owns'][0].removesuffix('.cs')+'.recovery-v5.md'
                guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
                unit['owns'] += [note,note+'.meta']
                unit['instructions']+=' Write '+note+' and '+note+'.meta (fileFormatVersion: 2 newline guid: '+guid+' newline) in addition to all original owned files. '
        if unit['id']=='TEST-HARNESS':
            unit['instructions']+=' Implement the v5 observation API: count actual ApplyAudio/ApplyQuality calls, maintain an active owned recording canvas, record lifecycle method ordering, reject overlapping street loads rather than silently auto-unloading. Readiness must inspect the actual shared wallet nested prefab and Outside/MarqueeBadge bindings as well as the original ten views, scene, private static font, geometry and animation references. Use no fabricated business state. '
    runtime=(source/old['spec_ref']).read_text(encoding='utf-8').replace('preview scene','isolated additive Editor scene').replace('temporary previews','owned temporary scenes')
    runtime+='\n### Requirement: Verified fixture compatibility\n\nThe test fixtures SHALL use the actual supported Editor APIs, activate their owned observation canvas, record real method calls and inspect shared-wallet, Outside and MarqueeBadge bindings without manufacturing game behavior. The target compiler rejects OpenPreviewScene; fixtures SHALL use owned additive Editor scenes with explicit cleanup and preserve preexisting scenes.\n\n#### Scenario: Observe the prepared boundary\n\n- **WHEN** readiness and UI acceptance execute\n- **THEN** fixtures use verified public APIs and prepared real references, actual pointer paths and faithful call observations\n- **AND** no destroyed object, inactive parent, fabricated count, seeding write or uninitialized service can substitute for the required observation\n'
    (spec/'spec.v5.md').write_text(runtime,encoding='utf-8',newline='')
    current['spec_ref']='specs/monopoly-game-lobby/spec.v5.md'; current['spec_sha256']=ref(current['spec_ref'])['sha256']
    observation=json.loads((spec/'presentation-observation.json').read_bytes())
    for view in observation['views']:
        if view['screen']=='Lobby':view['controls']+=['Outside','MarqueeBadge']
        if view['screen'] in ('Lobby','Recharge'):
            view['shared_wallet']='Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/SharedWallet_placeHolder.prefab'
            for name in ('Coins','Ingots','Primary'):
                if name not in view['controls']:view['controls'].append(name)
    wallet='Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/SharedWallet_placeHolder.prefab'
    # Tuanjie stores an opaque encoded guid in .meta; serialized prefab pointers
    # carry the actual Editor GUID. Verify both real nested source references,
    # preserving the imported metadata verbatim rather than decoding/rewriting it.
    wallet_guid=None
    for screen in ('Lobby','Recharge'):
        text=(source/('Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/'+screen+'View_placeHolder.prefab')).read_text()
        references=re.findall(r'm_SourcePrefab: \{fileID: 100100000, guid: ([0-9a-f]{32}), type: 3\}',text)
        if len(references)!=1 or (wallet_guid is not None and references[0]!=wallet_guid):
            raise ValueError('Shared wallet nested source references differ')
        wallet_guid=references[0]
    observation['repair']=completed; observation['shared_wallet_guid']=wallet_guid
    (spec/'presentation-observation.v5.json').write_text(json.dumps(observation,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    presentation=json.loads((source/old['presentation_ref']['path']).read_bytes())
    presentation['revision']=completed['candidate']
    presentation['files']=[ref(item['path']) for item in presentation['files']]
    additions=[wallet,wallet+'.meta','Editor/Script/LobbyRehearsal/LobbyPreparationRepair.cs','Editor/Script/LobbyRehearsal/LobbyPreparationRepair.cs.meta']
    presentation['files'] += [ref(path) for path in additions if path not in {p['path'] for p in presentation['files']}]
    (spec/'presentation.v5.json').write_text(json.dumps(presentation,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    current['presentation_ref']=ref('specs/monopoly-game-lobby/presentation.v5.json')
    profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
    for path in ['Runtime/Script/MonopolyRootScene.cs','package.json',guide,'specs/monopoly-game-lobby/test-harness-api.v5.txt']:
        if path not in {r['path'] for r in profile['rules']}:profile['rules'].append(ref(path))
    profile['protected_paths']=list(dict.fromkeys(profile['protected_paths']+additions+[guide,'package.json','Runtime/Script/MonopolyRootScene.cs','specs/monopoly-game-lobby/test-harness-api.v5.txt','specs/monopoly-game-lobby/presentation-observation.v5.json']))
    (spec/'coding-profile.v5.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v5.json')
    (spec/'contract.v5.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
    (framework/'.agent/lobby-apply.json').write_bytes(raw)
    context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    (spec/'planning-context.v5.json').write_text(json.dumps(context.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    contracts=[]; rules=UnityAdapter()
    for version in range(1,6):
        contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,
            previous=contracts[-1] if contracts else None,max_cycles=6))
    load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
    git(source,'add','specs/monopoly-game-lobby')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Freeze verified version-five presentation and fixture contract')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=3000000,output_limit=900000,max_cycles=6,max_added_units=2)
    lease=RunLease(state,'monopoly-game-lobby','cycle5-transition-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,
            workers_reconciled=lambda:all('actual' in c for c in budget._read()['calls'].values()) and not git(source,'status','--porcelain'))
        candidate=git(source,'rev-parse','HEAD').decode().strip()
        atomic_write(state,'current-execution.json',json.dumps({'version':5,'candidate':candidate,'contract_source':'architect-v5','contract_sha256':contracts[-1].sha256},indent=2).encode())
        print(json.dumps({'version':5,'baseline':candidate,'contract_sha256':contracts[-1].sha256,'retained_usage':budget.totals()}))
    finally:lease.release()


if __name__=='__main__':main()
