"""Prepare a consecutive recovery contract without modifying test behavior."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid5,NAMESPACE_URL
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git

framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='abandon' or result['contract_version']!=6:raise ValueError('Actual version-six abandonment required')
source=root/'worktrees/architect-v7'
if source.exists():raise ValueError('Preserve existing version-seven preparation; no implicit replay')
git(root/'module','worktree','add','-b','codex/lobby-architect-v7',str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby'
old=json.loads((spec/'contract.v6.json').read_bytes())
current=old|{'contract_version':7,'previous_contract_sha256':sha256((spec/'contract.v6.json').read_bytes()).hexdigest(),'ownership_migrations':[]}
unit=next(u for u in current['units'] if u['id']=='TEST-PRES-CORE')
note=unit['owns'][0].removesuffix('.cs')+'.repair-v7.md'
guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
unit['owns'] += [note,note+'.meta']
unit['instructions']+=' Version 7: preserve the current suite and repair the four actual independent findings in focused-repair.v7.md. Prioritize Story_L1_01, Story_L1_02, Story_L1_03, Story_L1_04, Story_L2_01 and their observation helpers; retain effective assertions in the other methods. Do not suppress real entry exceptions or replace failed observations with weaker oracles. Update the current acceptance map truthfully. Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Other historical provenance remains unchanged.'
guide='specs/monopoly-game-lobby/focused-repair.v7.md'
(source/guide).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby/focused-repair.v7.md').read_bytes())
def ref(p):return {'path':p,'sha256':sha256((source/p).read_bytes()).hexdigest()}
profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
profile['rules'].append(ref(guide));profile['protected_paths'].append(guide)
(spec/'coding-profile.v7.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v7.json')
(spec/'contract.v7.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
contracts=[];rules=UnityAdapter()
for version in range(1,8):contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=12))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
git(source,'add','specs/monopoly-game-lobby')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare authorized version-seven focused test repair')
print(json.dumps({'version':7,'baseline':git(source,'rev-parse','HEAD').decode().strip(),'contract_sha256':contracts[-1].sha256,'test_behavior_changed_by_architect':False}))
