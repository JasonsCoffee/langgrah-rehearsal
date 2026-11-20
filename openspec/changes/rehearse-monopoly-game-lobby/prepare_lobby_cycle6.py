"""Bounded specialist split with explicit ownership/lineage migrations."""
from hashlib import sha256
import json
import os
from pathlib import Path
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
    framework=Path.cwd().resolve(); root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state'; run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    if result['outcome']!='rework' or result['contract_version']!=5:raise ValueError('Actual version-five rework required')
    checkpoint=json.loads((run/'services-v5/state.json').read_bytes())
    if checkpoint['tdd']['frozen'] is not None:raise ValueError('Never replace frozen tests')
    source=root/'worktrees/architect-v6'
    if source.exists():raise ValueError('Preserve existing version-six worktree; reconcile explicitly')
    git(root/'module','worktree','add','-b','codex/lobby-architect-v6',str(source),result['candidate_revision'])
    spec=source/'specs/monopoly-game-lobby'
    old=json.loads((spec/'contract.v5.json').read_bytes())
    current=old|{'contract_version':6,'previous_contract_sha256':sha256((spec/'contract.v5.json').read_bytes()).hexdigest()}
    retired=next(u for u in current['units'] if u['id']=='TEST-SHELL')
    retired['status']='superseded'
    original=source/'Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationTests.cs'
    (spec/'rejected-presentation-v5.cs.txt').write_bytes(original.read_bytes())
    original.write_text('// Historical compile-only container; active mapped tests moved to specialist units.\nnamespace jj.Monopoly.Tests.LobbyRehearsal { public sealed class LobbyPresentationTests { } }\n',encoding='utf-8',newline='')
    def map_id(test):
        if '.LobbyPresentationTests.' not in test:return test
        return test.replace('.LobbyPresentationTests.','.LobbyPresentationNfrTests.' if test.rsplit('.',1)[-1].startswith('Story_NFR_') else '.LobbyPresentationCoreTests.')
    core_history=[p for p in retired['owns'] if '.recovery-v5.md' not in p]
    nfr_history=[p for p in retired['owns'] if '.recovery-v5.md' in p]
    additions=[]; meta=[]
    for suffix,cls,history in [('CORE','LobbyPresentationCoreTests',core_history),('NFR','LobbyPresentationNfrTests',nfr_history)]:
        path='Tests/Runtime/Script/LobbyRehearsal/'+cls+'.cs'
        (source/path).write_text('// Compile-only specialist container; all assertions are delegated.\nnamespace jj.Monopoly.Tests.LobbyRehearsal { public sealed class '+cls+' { } }\n',encoding='utf-8',newline='')
        (source/(path+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+path).hex+'\n',encoding='utf-8',newline='')
        meta.append(path+'.meta')
        note=path.removesuffix('.cs')+'.acceptance.md'; guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
        accepted=[map_id(t) for t in retired['acceptance'] if (t.rsplit('.',1)[-1].startswith('Story_NFR_'))==(suffix=='NFR')]
        unit=dict(id='TEST-PRES-'+suffix,role='test',status='active',title='Focused presentation '+suffix.lower()+' acceptance',
            spec_ref='LOBBY',owns=[path,note,note+'.meta']+history,acceptance=accepted,depends_on=['TEST-HARNESS'],
            interfaces=[{'symbol':'jj.Monopoly.Tests.LobbyRehearsal.'+cls,'signature':'class '+cls}],
            add_justification='Two native rework dossiers show combined UI/NFR authorship repeatedly misses contradictory lifecycle and boundary assertions; split the unchanged twelve acceptance methods into two independently reviewed specialists.',
            instructions='Author only the '+suffix+' methods listed in acceptance, using the real shared LobbyHarness and test-author-plan.v6.md. Read every mapped original acceptance clause and verified v5 fixture guidance. Start from the compiling container, not the rejected historical suite. Do not fabricate service or coordinator outcomes in adapters. Nonfunctional runtime stubs must fail through effective assertions, not fixture/setup errors. Keep every existing public API. Write '+path+', '+note+' and '+note+'.meta (fileFormatVersion: 2 newline guid: '+guid+' newline). Other owned files are historical provenance: preserve their existing bytes; do not reactivate the retired class or use obsolete notes as current coverage. The new acceptance note must map each clause to exact effective assertions. Do not implement game business code.')
        additions.append(unit)
    index=current['units'].index(retired)+1
    current['units'][index:index]=additions
    current['ownership_migrations']=[{'from_unit':'TEST-SHELL','to_unit':unit['id'],'paths':history,
        'rationale':'Retain the rejected author provenance and repair/accounting lineage under each bounded specialist.'}
        for unit,history in zip(additions,(core_history,nfr_history))]
    for u in current['units']:
        if u['role']=='impl':u['acceptance']=[map_id(t) for t in u['acceptance']]
    for link in current['test_links']:
        link['test_id']=map_id(link['test_id'])
        if link['author_unit']=='TEST-SHELL':link['author_unit']='TEST-PRES-NFR' if '.Story_NFR_' in link['test_id'] else 'TEST-PRES-CORE'
    for link in current['task_links']:
        if 'TEST-SHELL' in link['unit_ids']:
            link['unit_ids']=[u for u in link['unit_ids'] if u!='TEST-SHELL']+['TEST-PRES-CORE','TEST-PRES-NFR']
    for name in ('story-test-map','acceptance-conditions'):
        previous=spec/(name+('.v2' if name=='acceptance-conditions' else '')+'.json')
        records=json.loads(previous.read_bytes())
        for row in records:row['test']=map_id(row['test'])
        (spec/(name+'.v6.json')).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    plan='specs/monopoly-game-lobby/test-author-plan.v6.md'
    (source/plan).write_bytes((framework/'openspec/changes/rehearse-monopoly-game-lobby/test-author-plan.v6.md').read_bytes())
    def ref(p):return {'path':p,'sha256':sha256((source/p).read_bytes()).hexdigest()}
    profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
    profile['rules'].append(ref(plan))
    profile['protected_paths']=list(dict.fromkeys(profile['protected_paths']+meta+[plan,'specs/monopoly-game-lobby/story-test-map.v6.json','specs/monopoly-game-lobby/acceptance-conditions.v6.json']))
    (spec/'coding-profile.v6.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
    current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v6.json')
    (spec/'contract.v6.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
    (framework/'.agent/lobby-apply.json').write_bytes(raw)
    context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
    contracts=[];rules=UnityAdapter()
    for version in range(1,7):contracts.append(load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=6))
    load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
    git(source,'add','Tests/Runtime/Script/LobbyRehearsal','specs/monopoly-game-lobby')
    git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare final bounded cycle with specialist test authors and explicit lineage')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=3000000,output_limit=900000,max_cycles=6,max_added_units=2)
    lease=RunLease(state,'monopoly-game-lobby','cycle6-transition-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,
            workers_reconciled=lambda:all('actual' in c for c in budget._read()['calls'].values()) and not git(source,'status','--porcelain'))
        candidate=git(source,'rev-parse','HEAD').decode().strip()
        atomic_write(state,'current-execution.json',json.dumps({'version':6,'candidate':candidate,'contract_source':'architect-v6','contract_sha256':contracts[-1].sha256},indent=2).encode())
        print(json.dumps({'version':6,'candidate':candidate,'contract_sha256':contracts[-1].sha256,'test_links':len(current['test_links']),'new_units':2,'retained_usage':budget.totals()}))
    finally:lease.release()


if __name__=='__main__':main()
