"""Prepare consecutive recovery artifacts; no implementation or model calls."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import NAMESPACE_URL, uuid5

from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.contracts import load_contract
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve()
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state'
    run=state/'.agent/runs/monopoly-game-lobby'
    outcome=json.loads((run/'result.json').read_bytes())
    if outcome['outcome']!='abandon' or outcome['contract_version']!=3:
        raise ValueError('Expected the inspected cycle-three abandonment')
    source=root/'worktrees/architect-v4'
    if source.exists():
        raise ValueError('Preserve existing preparation; no implicit replay')
    retained=outcome['candidate_revision']
    branch='agent/monopoly-game-lobby/cycle-3'
    if git(root/'module','rev-parse',branch).decode().strip()!=retained:
        raise ValueError('Retained cycle ref differs from the terminal candidate')
    git(root/'module','worktree','add','-b','codex/lobby-architect-v4',str(source),retained)
    spec=source/'specs/monopoly-game-lobby'
    old=json.loads((spec/'contract.v3.json').read_bytes())
    current=old|{'contract_version':4,'previous_contract_sha256':sha256((spec/'contract.v3.json').read_bytes()).hexdigest()}
    findings={}
    receipts=sorted((run/'model-calls').glob('*.json'),key=lambda p:p.stat().st_mtime)
    for path in receipts:
        record=json.loads(path.read_bytes())
        if record['identity']['role']!='judge' or 'reply' not in record:continue
        try: decision=json.loads(record['reply']['text'])
        except ValueError:continue
        if decision.get('valid') is False:
            findings.setdefault(record['identity']['unit_id'],[]).append(decision['explanation'])
    for unit in current['units']:
        if unit['role']!='test':continue
        note=unit['owns'][0].removesuffix('.cs')+'.recovery-v4.md'
        guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
        unit['owns'] += [note,note+'.meta']
        unit['instructions'] += (' Recovery cycle 4: retained prior tests were NEVER globally frozen; repair their actual rejected behavior and acceptance maps. '
            'Review the supplied prior independent findings for this unit. Do not repeat false claims, skipped branches, self-comparisons or fabricated fake-port business state. '
            'In addition to every original owned artifact, write '+note+' with a concise truthful repair/coverage explanation, and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. '
            'The new note intentionally starts absent so native preparation delegates the repair before reviewing it. Preserve all prepared public APIs. '
            'Tests assert desired behavior of the nonfunctional runtime shells; they are expected to fail behaviorally before implementation, not to make the stubs pass. '
            'All scene assets live under Runtime/Resource/monopoly/Scenes/LobbyRehearsal; only prefab/configuration assets live under UI/Prefabs/LobbyRehearsal. '
            'Use actual DTO/view/serialized-control names supplied in context. A test must give nonempty realistic stimuli for each mapped acceptance clause.')
    report={u['id']:findings.get(u['id'],[])[-2:] for u in current['units'] if u['role']=='test'}
    (spec/'test-preparation-findings.v4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    for name in ('proposal.md','design.md'):
        (spec/name).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby'/name).read_bytes())
    (spec/'contract.v4.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
    (framework/'.agent/lobby-apply.json').write_bytes(raw)
    context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    (spec/'planning-context.v4.json').write_text(json.dumps(context.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    previous=None
    rules=UnityAdapter()
    for version in (1,2,3,4):
        previous=load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,previous=previous,max_cycles=6)
    profile=load_profile((source/previous.coding_profile_ref.path).read_bytes(),source,rules=rules,
        allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',))
    profile.validate_contract(previous)
    git(source,'add','specs/monopoly-game-lobby')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare authorized cycle-four recovery without implementation')
    print(json.dumps({'version':4,'contract_sha256':previous.sha256,'baseline':git(source,'rev-parse','HEAD').decode().strip(),
        'retained_parent':retained,'units':len(previous.units),'tests':len(previous.test_links),'new_run':False}))


if __name__=='__main__':main()
