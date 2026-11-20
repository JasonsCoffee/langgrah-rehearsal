"""Split existing delegated test methods mechanically at a contract boundary."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid5,NAMESPACE_URL
from tree_sitter import Language,Parser
import tree_sitter_c_sharp
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git
from operational_transport import retained_transport_failure

framework=Path.cwd().resolve();root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework' or result['contract_version']!=13:raise ValueError('Actual cycle-thirteen rework required')
if json.loads((run/'services-v13/state.json').read_bytes())['tdd']['frozen'] is not None:raise ValueError('Never split globally frozen tests')
source=root/'worktrees/architect-v14'
if source.exists():raise ValueError('Preserve existing preparation')
git(root/'module','worktree','add','-b','codex/lobby-architect-v14',str(source),result['candidate_revision'])
spec=source/'specs/monopoly-game-lobby';old_path=spec/'contract.v13.json';old=json.loads(old_path.read_bytes())
current=old|{'contract_version':14,'previous_contract_sha256':sha256(old_path.read_bytes()).hexdigest()}
retired=next(u for u in current['units'] if u['id']=='TEST-ECON');retired['status']='superseded'
primary='Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyTests.cs'
secondary='Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyRechargeTests.cs'
raw=(source/primary).read_bytes();parser=Parser(Language(tree_sitter_c_sharp.language()));tree=parser.parse(raw)
if tree.root_node.has_error:raise ValueError('Mechanical split requires syntactically valid delegated source')
def methods(data):
    parsed=parser.parse(data)
    if parsed.root_node.has_error:raise ValueError('Split source must parse')
    found={}
    def visit(node):
        if node.type=='method_declaration' and any(child.type=='attribute_list' and b'[Test]' in child.text for child in node.children):
            name=node.child_by_field_name('name').text.decode()
            if name in found:raise ValueError('Duplicate source method')
            found[name]=(node.start_byte,node.end_byte,node.text)
        for child in node.children:visit(child)
    visit(parsed.root_node);return found
before=methods(raw)
if len(before)!=34 or sum(name.startswith('Story_L12_') for name in before)!=11:raise ValueError('Unexpected test inventory')
moved={name:value for name,value in before.items() if name.startswith('Story_L12_')}
base=raw
for start,end,_ in sorted(moved.values(),reverse=True):base=base[:start]+b'\n'+base[end:]
marker=b'public sealed class LobbyEconomyTests'
if base.count(marker)!=1:raise ValueError('Unexpected class declaration')
base=base.replace(marker,b'public sealed partial class LobbyEconomyTests',1)
usings=b'\n'.join(node.text for node in tree.root_node.children if node.type=='using_directive')
part=usings+b'\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed partial class LobbyEconomyTests\n    {\n'
part+=b'\n\n'.join(value[2] for _,value in sorted(moved.items()))+b'\n    }\n}\n'
after=methods(base)|methods(part)
if set(after)!=set(before) or any(after[name][2]!=before[name][2] for name in before):raise ValueError('A delegated method body changed during preparation')
(source/primary).write_bytes(base);(source/secondary).write_bytes(part)
(source/(secondary+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+secondary).hex+'\n',encoding='utf-8',newline='')
(spec/'economy-source-split.v14.json').write_text(json.dumps({'original_source_sha256':sha256(raw).hexdigest(),
    'method_sha256':{name:sha256(value[2]).hexdigest() for name,value in before.items()},
    'destination':{name:secondary if name in moved else primary for name in before},'all_34_method_bodies_byte_identical':True},indent=2),encoding='utf-8',newline='')
history_cards=[p for p in retired['owns'] if '.recovery-v4.md' in p]
history_appear=[p for p in retired['owns'] if p not in history_cards]
finding=json.loads((run/'dossier-v13.json').read_bytes())['failed_units'][0]['hypothesis']
units=[]
for key,owns,path,groups in [('APPEAR',history_appear,primary,('L3','L7')),('CARDS',history_cards,secondary,('L12',))]:
    accepted=[test for test in retired['acceptance'] if ('.Story_L12_' in test)==(key=='CARDS')]
    note=path.removesuffix('.cs')+('.repair-v14.md' if key=='APPEAR' else '.acceptance.md')
    owned=list(dict.fromkeys([path,note,note+'.meta']+owns));guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    current_map=primary.removesuffix('.cs')+'.acceptance.md' if key=='APPEAR' else note
    instructions=('Repair only the mapped '+('/'.join(groups))+' tests'+(' and Journey_ECON' if key=='APPEAR' else '')+
        ' in the existing partial LobbyEconomyTests class. The split preserves all existing test method bodies byte-for-byte; this is not permission to discard effective assertions. '+
        'Shared private helpers live in LobbyEconomyTests.cs; CARDS receives those read-only and may add distinct helper methods in its own partial file. '+
        'Use the actual reviewed LobbyHarness and current v5 observation/API guidance; never fabricate business outcomes. Tests are not globally frozen. '+
        'Repair the applicable latest independent findings: '+finding+
        ' Preserve every other unit and historical note. Do not change methods assigned to the other partial file. '+
        'Write strict JSON files/reason with complete owned file values. Update '+current_map+' with clause-level effective assertions for only this specialist. '+
        'Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. '+
        'Do not implement game business behavior. Keep all public APIs and exact existing test IDs. Account entry and cleanup must be awaited safely.')
    unit=dict(id='TEST-'+key,role='test',status='active',title='Focused '+key.lower()+' acceptance',spec_ref='LOBBY',
        owns=owned,acceptance=accepted,depends_on=['TEST-HARNESS']+(['TEST-APPEAR'] if key=='CARDS' else []),interfaces=[],
        add_justification='Three whole-suite economy revisions exhausted source preparation while leaving nine independent coverage areas incomplete; split the same 34 IDs into 23 appearance/shop/journey and 11 recharge/card/VIP methods, preserving all method bytes and inherited repair history.',instructions=instructions)
    units.append(unit)
index=current['units'].index(retired)+1;current['units'][index:index]=units
current['ownership_migrations']=[{'from_unit':'TEST-ECON','to_unit':unit['id'],'paths':history,'rationale':'Preserve original ownership provenance and repair lineage under the bounded specialists.'} for unit,history in zip(units,(history_appear,history_cards))]
for link in current['test_links']:
    if link['author_unit']=='TEST-ECON':link['author_unit']='TEST-CARDS' if '.Story_L12_' in link['test_id'] else 'TEST-APPEAR'
for link in current['task_links']:
    if 'TEST-ECON' in link['unit_ids']:link['unit_ids']=[u for u in link['unit_ids'] if u!='TEST-ECON']+['TEST-APPEAR','TEST-CARDS']
def ref(path):return {'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
profile['protected_paths'].append(secondary+'.meta')
(spec/'coding-profile.v14.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v14.json')
(spec/'contract.v14.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter();contracts=[]
for n in range(1,15):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=30))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
if rules.parse_check({primary:base,secondary:part}):raise ValueError('Split containers must parse')
git(source,'add','Tests/Runtime/Script/LobbyRehearsal','specs/monopoly-game-lobby')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Split unfrozen economy authorship with byte-preserved methods and lineage')
raw_apply=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw_apply)
context=discover_context(framework,json.loads(raw_apply),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
policy=json.loads((state/'budget-policy.json').read_bytes())
budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
def reconciled():
    ledger=json.loads((run/'budget.json').read_bytes())
    for call_id,call in ledger['calls'].items():
        if 'actual' in call:continue
        if call_id!='v8-step3-prepare-review-TEST-PRES-CORE':return False
        retained_transport_failure(json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()),call,8)
    return json.loads((run/'services-v13/effects/transaction.json').read_bytes()).get('complete') is True and not git(source,'status','--porcelain')
lease=RunLease(state,'monopoly-game-lobby','cycle14-transition-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
try:
    transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
    active={'version':14,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v14','contract_sha256':contracts[-1].sha256}
    atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
    print(json.dumps(active|{'preserved_usage':budget.totals(),'test_ids_unchanged':len(current['test_links']),'byte_preserved_methods':len(before),'new_units':2}))
finally:lease.release()
