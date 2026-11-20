"""Prepare audited token recovery and an observation-only formatter API seam."""
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
if result['outcome']!='abandon' or result['contract_version']!=7:raise ValueError('Actual version-seven budget stop required')
source=root/'worktrees/architect-v8'
if source.exists():raise ValueError('Preserve existing version-eight preparation; reconcile explicitly')
git(root/'module','worktree','add','-b','codex/lobby-architect-v8',str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby'
old=json.loads((spec/'contract.v7.json').read_bytes())
current=old|{'contract_version':8,'previous_contract_sha256':sha256((spec/'contract.v7.json').read_bytes()).hexdigest(),'ownership_migrations':[]}
ports='Runtime/Script/UI/LobbyRehearsal/LobbyPorts.cs';economy='Runtime/Script/UI/LobbyRehearsal/LobbyEconomy.cs'
p=source/ports;s=p.read_text(encoding='utf-8');s=s.replace('public interface ILobbyEconomy\n    {','public interface ILobbyEconomy\n    {\n        event Action<long> BalanceFormatted;');p.write_text(s,encoding='utf-8',newline='')
p=source/economy;s=p.read_text(encoding='utf-8');s=s.replace('public sealed class LobbyEconomy : ILobbyEconomy\n    {','public sealed class LobbyEconomy : ILobbyEconomy\n    {\n        public event Action<long> BalanceFormatted;');p.write_text(s,encoding='utf-8',newline='')
for path in (ports,economy):
    if 'event Action<long> BalanceFormatted;' not in (source/path).read_text():raise ValueError('Prepared observation declaration missing')
guide='specs/monopoly-game-lobby/focused-repair.v8.md'
(source/guide).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby/focused-repair.v8.md').read_bytes())
unit=next(u for u in current['units'] if u['id']=='TEST-PRES-CORE')
note=unit['owns'][0].removesuffix('.cs')+'.repair-v8.md';guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
unit['owns'] += [note,note+'.meta']
unit['instructions']+=' Version 8 supersedes the prior IL-specific approach: use the prepared BalanceFormatted observation event as described in focused-repair.v8.md, repair the actual C# and current acceptance map, and preserve effective existing assertions. The owned test source is not globally frozen yet. Do not return only notes. Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline.'
next(u for u in current['units'] if u['id']=='ECON')['instructions']+=' The prepared BalanceFormatted event is observation-only: raise it exactly once per actual FormatBalance(long) invocation, preserving the specified common currency formatting behavior.'
def ref(p):return {'path':p,'sha256':sha256((source/p).read_bytes()).hexdigest()}
profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
profile['rules']=[ref(r['path']) if r['path']==ports else r for r in profile['rules']]
profile['rules'].append(ref(guide));profile['protected_paths'].append(guide)
(spec/'coding-profile.v8.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v8.json')
presentation=json.loads((source/old['presentation_ref']['path']).read_bytes())
presentation['files']=[ref(r['path']) if r['path']==ports else r for r in presentation['files']]
(spec/'presentation.v8.json').write_text(json.dumps(presentation,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
current['presentation_ref']=ref('specs/monopoly-game-lobby/presentation.v8.json')
(spec/'contract.v8.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
contracts=[];rules=UnityAdapter()
for version in range(1,9):contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=12))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
violations=rules.parse_check({p:(source/p).read_bytes() for p in (ports,economy)})
if violations:raise ValueError('Prepared observation declarations do not parse')
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
git(source,'add','specs/monopoly-game-lobby',ports,economy)
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare explicit token recovery and observable common formatter seam')
print(json.dumps({'version':8,'baseline':git(source,'rev-parse','HEAD').decode().strip(),'contract_sha256':contracts[-1].sha256,'functional_implementation_written':False}))
