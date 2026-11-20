"""Prepare missing presentation bindings before the next contract is frozen."""
from pathlib import Path
import json
import os
from uuid import uuid5,NAMESPACE_URL
from unity_coder.core.workspaces import git

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
framework=Path.cwd().resolve()
run=root/'trusted-state/.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework' or result['contract_version']!=4:
    raise ValueError('Expected the actual version-four contract rework dossier')
saved=json.loads((run/'services-v4/state.json').read_bytes())
if saved['tdd']['frozen'] is not None:
    raise ValueError('Never replace frozen tests during baseline preparation')
source=root/'worktrees/architect-v5'
if source.exists():raise ValueError('Existing preparation must be preserved and reconciled')
git(root/'module','worktree','add','-b','codex/lobby-architect-v5',str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby'
test=source/'Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationTests.cs'
(spec/'rejected-presentation-v4.cs.txt').write_bytes(test.read_bytes())
test.write_text('// Compile-only container. The configured test author supplies all behavioral assertions.\nnamespace jj.Monopoly.Tests.LobbyRehearsal { public sealed class LobbyPresentationTests { } }\n',encoding='utf-8',newline='')
path='Editor/Script/LobbyRehearsal/LobbyPreparationRepair.cs'
(source/path).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby/LobbyPreparationRepair.cs').read_bytes())
(source/(path+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+path).hex+'\n',encoding='utf-8',newline='')
(source/'package.json').write_bytes((Path(os.environ['UNITY_HOST'])/'Assets/JJGame/monopoly/package.json').read_bytes())
git(source,'add','Editor/Script/LobbyRehearsal','Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationTests.cs','specs/monopoly-game-lobby','package.json')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare version-five asset repair and nonfunctional test container')
print('Prepared',git(source,'rev-parse','HEAD').decode().strip(),'without functional implementation or frozen-test changes')
