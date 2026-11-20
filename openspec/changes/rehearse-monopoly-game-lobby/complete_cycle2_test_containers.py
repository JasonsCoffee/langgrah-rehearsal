"""Prepare assertion-free containers and author-owned acceptance maps for cycle 2."""
import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL,uuid5
from unity_coder.core.contracts import load_contract
from unity_coder.core.workspaces import git
from unity_coder.adapters.unity import UnityAdapter

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
source=root/'worktrees/architect-v2'
spec=source/'specs/monopoly-game-lobby'
if (root/'trusted-state/current-execution.json').exists():
    raise ValueError('Cycle already activated; containers cannot be rewritten')
contract=json.loads((spec/'contract.v2.json').read_bytes())
for unit in contract['units']:
    if unit['role']!='test': continue
    code=unit['owns'][0]
    name=Path(code).stem
    if len(unit['owns'])!=1:
        raise ValueError('Author artifacts already prepared; no replay')
    # The v1 rejected body is retained in its native cycle branch and Git parent.
    # These are import/compile containers, with zero assertions or [Test] methods.
    (source/code).write_text('// Compile-only preparation container; the configured test author supplies all assertions.\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed class '+name+' { }\n}\n',encoding='utf-8',newline='')
    checklist=code.removesuffix('.cs')+'.acceptance.md'
    metadata=checklist+'.meta'
    guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/cycle2/'+checklist).hex
    unit['owns'] += [checklist,metadata]
    unit['instructions']+=' Write all three owned files: complete C# tests, an acceptance checklist mapping every source clause to named assertions and observable outputs, and its Unity metadata. The checklist is deliberately absent initially so native prepare dispatches the author before review. Its metadata must be exactly fileFormatVersion: 2 followed by guid: '+guid+' (two newline-terminated lines). Use CustomAttributeData.ConstructorArguments to inspect routing/binding attributes; do not invent a ViewRouterAttribute.Path property. The old rejected v1 test body is not a template to retain. For deliberately unimplemented SUT entry methods, assert successful invocation with Assert.DoesNotThrow before checking lifecycle outcomes; keep fixture setup independent of unimplemented services.'
(spec/'contract.v2.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter()
previous=load_contract((spec/'contract.v1.json').read_bytes(),source,rules)
current=load_contract((spec/'contract.v2.json').read_bytes(),source,rules,previous=previous)
git(source,'add','.')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Complete cycle 2 test containers and delegated acceptance artifacts')
print('Validated final cycle-2 draft',current.sha256,'with assertion-free import containers')
