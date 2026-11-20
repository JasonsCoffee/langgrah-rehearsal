"""Prepare the consecutive authorized recovery without writing test behavior."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid5,NAMESPACE_URL
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git

framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
run=root/'trusted-state/.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='abandon' or result['contract_version']!=12 or result['reason']!='budget':
    raise ValueError('The actual version-twelve budget abandonment is required')
source=root/'worktrees/architect-v13'
if source.exists():raise ValueError('Preserve existing preparation; reconcile explicitly')
git(root/'module','worktree','add','-b','codex/lobby-architect-v13',str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby';old_path=spec/'contract.v12.json'
old=json.loads(old_path.read_bytes())
current=old|{'contract_version':13,'previous_contract_sha256':sha256(old_path.read_bytes()).hexdigest(),'ownership_migrations':[]}
dossier=json.loads((run/'dossier-v12.json').read_bytes())
for finding in dossier['failed_units']:
    unit=next(u for u in current['units'] if u['id']==finding['id'])
    if unit['role']!='test':raise ValueError('Expected the actual test-preparation dossier')
    note=next(p for p in unit['owns'] if p.endswith('.cs')).removesuffix('.cs')+'.repair-v13.md'
    unit['owns'] += [note,note+'.meta']
    guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    # Retain historical contracts verbatim; active instructions use the latest
    # actual findings instead of piling contradictory old repair requests.
    unit['instructions']=unit['instructions'].split(' Current cycle ',1)[0]
    unit['instructions']+=' Current cycle 13: repair the actual current C# and acceptance map for these latest independent findings: '+finding['hypothesis']+' Preserve the effective NFR_02-04 assertions and all other current coverage. Tests are not globally frozen yet; no production behavior may be written by this unit. The existing Navigator and UserDefault injection properties are the supported framework observation boundaries. Return strict JSON with files and reason, escaping every quote, backslash and control character. Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Do not return only notes.'
for name in ('proposal.md','design.md'):(spec/name).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby'/name).read_bytes())
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
(spec/'planning-context.v13.json').write_text(json.dumps(context.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8',newline='')
(spec/'contract.v13.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter();contracts=[]
for n in range(1,14):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=30))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
git(source,'add','specs/monopoly-game-lobby')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare authorized thirty-cycle same-run recovery')
print(json.dumps({'version':13,'baseline':git(source,'rev-parse','HEAD').decode().strip(),'contract_sha256':contracts[-1].sha256,'test_behavior_written':False}))
