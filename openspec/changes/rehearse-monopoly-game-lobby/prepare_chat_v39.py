"""Byte-preserving test partition and nonfunctional fake-platform inputs."""
from copy import deepcopy
from hashlib import sha256
import json
from collections import Counter
from pathlib import Path
from uuid import NAMESPACE_URL,uuid5
from tree_sitter import Language,Parser
import tree_sitter_c_sharp


def prepare(source: Path,current: dict,dossier: dict) -> None:
    if current['contract_version']!=39 or {u['id'] for u in dossier['failed_units']}!={'TEST-CHAT'}:
        raise ValueError('Only the inspected Chat-source rework may be prepared')
    parser=Parser(Language(tree_sitter_c_sharp.language()))
    prefix='Tests/Runtime/Script/LobbyRehearsal/';primary=prefix+'LobbySocialChatTests.cs'
    raw=(source/primary).read_bytes();tree=parser.parse(raw)
    if tree.root_node.has_error:raise ValueError('Malformed source cannot be partitioned')
    def methods(data):
        found={}
        def visit(node):
            if node.type=='method_declaration' and any(c.type=='attribute_list' and b'[Test]' in c.text for c in node.children):
                name=node.child_by_field_name('name').text.decode()
                if name in found:raise ValueError('Duplicate test method')
                found[name]=(node.start_byte,node.end_byte,node.text)
            for child in node.children:visit(child)
        parsed=parser.parse(data)
        if parsed.root_node.has_error:raise ValueError('Partition syntax invalid')
        visit(parsed.root_node);return found
    before=methods(raw)
    mapped={'Story_L13_'+str(n).zfill(2) for n in range(1,14)}|{'Journey_SOCIAL'}
    companions={'Story_L13_02_Cap','Story_L13_03_Wrap','Story_L13_06_Pending','Story_L13_07_Empty'}
    if set(before)!=mapped|companions:raise ValueError('Expected all fourteen mapped and four companion methods')
    old=next(u for u in current['units'] if u['id']=='TEST-CHAT');original=deepcopy(old)
    parts={
        'TEST-CHAT-MSG':(prefix+'LobbyChatMessageTests.cs',{'Story_L13_06','Story_L13_08','Story_L13_12','Story_L13_13','Story_L13_06_Pending'},'.recovery-v4.md'),
        'TEST-CHAT-STATE':(prefix+'LobbyChatStateTests.cs',{'Story_L13_07','Story_L13_09','Story_L13_10','Story_L13_11','Journey_SOCIAL','Story_L13_07_Empty'},'.focused-v23.md'),
    }
    all_nodes=[]
    def collect_methods(node):
        if node.type=='method_declaration':all_nodes.append(node)
        for child in node.children:collect_methods(child)
    collect_methods(tree.root_node)
    names={n.child_by_field_name('name').text.decode() for n in all_nodes}
    graph={name:set() for name in names}
    for method in all_nodes:
        name=method.child_by_field_name('name').text.decode()
        def references(node):
            if node.type=='identifier' and node.text.decode() in names:graph[name].add(node.text.decode())
            for child in node.children:references(child)
        references(method)
    roots=[set(before)-set.union(*(part[1] for part in parts.values()))]+[part[1] for part in parts.values()]
    reachable=[]
    for root_names in roots:
        seen=set();pending=list(root_names)
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name);pending.extend(graph.get(name,set())-seen)
        reachable.append(seen)
    for index,(unit_id,(path,root_names,history)) in enumerate(list(parts.items()),1):
        exclusive={name for name in reachable[index] if sum(name in r for r in reachable)==1}
        if not root_names<=exclusive:raise ValueError('A test method is called by a peer test scope')
        parts[unit_id]=(path,exclusive,history)
    using_nodes=[]
    def collect_usings(node):
        if node.type=='using_directive':using_nodes.append(node.text)
        for child in node.children:collect_usings(child)
    collect_usings(tree.root_node)
    usings=b'\n'.join(dict.fromkeys(using_nodes))
    base=raw;proofs=[];new_units=[];moved_names=set()
    finding=dossier['failed_units'][0]['hypothesis']
    rationale='The actual fourteen-clause Chat author exhausted three source reviews, with four extra companions outside the mapped selection. Narrow presentation, sending and conversation/state responsibilities while preserving all eighteen existing method bodies and all fourteen mapped IDs. Shared helper repair remains with the primary author.'
    for unit_id,(path,numbers,history_suffix) in parts.items():
        selected={n:v for n,v in before.items() if n in numbers};moved_names.update(selected)
        selected_nodes=[n for n in all_nodes if n.child_by_field_name('name').text.decode() in numbers]
        data=usings+b'\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed partial class LobbySocialTests\n    {\n'+b'\n\n'.join(n.text for n in selected_nodes)+b'\n    }\n}\n'
        if (source/path).exists():raise ValueError('Preserve existing partial')
        (source/path).write_bytes(data)
        (source/(path+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+path).hex+'\n',encoding='utf-8',newline='')
        history=[p for p in original['owns'] if p.endswith(history_suffix) or p.endswith(history_suffix+'.meta')]
        if len(history)!=2 or any(not (source/p).exists() for p in history):raise ValueError('Existing history pair required for inherited lineage')
        old['owns']=[p for p in old['owns'] if p not in history]
        acceptance=[t for t in original['acceptance'] if t.rsplit('.',1)[1] in selected]
        note=path.removesuffix('.cs')+'.focused-v39.md';guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
        unit=dict(id=unit_id,role='test',status='active',title='Focused '+unit_id.lower()+' acceptance',spec_ref='LOBBY',
            owns=[path]+history+[note,note+'.meta'],acceptance=acceptance,
            depends_on=list(dict.fromkeys(original['depends_on']+['TEST-CHAT'])),interfaces=[],add_justification=rationale,
            instructions='Author only your '+str(len(acceptance))+' mapped methods in the owned partial. Every existing method body is byte-identical to the previous delegated source. Shared private helpers in other partials are read-only. Preserve every effective assertion and all source clauses; repair only findings relevant to your mapped methods. Read chat-authoring.v39.md. Expected assertions against nonfunctional services are required baseline Red, not invented business implementation. Consolidate effective companion coverage into your mapped methods; no acceptance credit comes from unmapped companions. Historical transferred notes stay byte-identical. Current actual findings: '+finding+' Write '+note+' as a truthful current clause map and '+note+'.meta with fileFormatVersion: 2 newline guid: '+guid+' newline. Use the host hash-bound edit protocol, never game business implementation or conditional coverage bypasses.')
        new_units.append(unit)
        current['ownership_migrations'].append(dict(from_unit='TEST-CHAT',to_unit=unit_id,paths=history,rationale='Preserve inherited repair lineage while narrowing test authorship; no assertion edits.'))
        for link in current['test_links']:
            if link['author_unit']=='TEST-CHAT' and link['test_id'].rsplit('.',1)[1] in selected:link['author_unit']=unit_id
        for link in current['task_links']:
            if 'TEST-CHAT' in link['unit_ids']:link['unit_ids'].append(unit_id)
        proofs.append({'unit':unit_id,'path':path,'methods':list(selected),'method_sha256':{n:sha256(v[2]).hexdigest() for n,v in selected.items()},'transferred_history_sha256':{p:sha256((source/p).read_bytes()).hexdigest() for p in history}})
    moved_helpers=set.union(*(part[1] for part in parts.values()))
    for start,end in sorted(((n.start_byte,n.end_byte) for n in all_nodes if n.child_by_field_name('name').text.decode() in moved_helpers),reverse=True):base=base[:start]+b'\n'+base[end:]
    (source/primary).write_bytes(base)
    after=methods(base)
    for path,_,_ in parts.values():
        for name,value in methods((source/path).read_bytes()).items():
            if name in after:raise ValueError('Partition duplicated a method')
            after[name]=value
    if set(after)!=set(before) or any(after[n][2]!=v[2] for n,v in before.items()):raise ValueError('Chat partition changed an assertion body')
    original_method_hashes=Counter(sha256(n.text).hexdigest() for n in all_nodes)
    partition_method_hashes=Counter()
    for data in [base]+[(source/path).read_bytes() for path,_,_ in parts.values()]:
        def check_methods(node):
            if node.type=='method_declaration':partition_method_hashes[sha256(node.text).hexdigest()]+=1
            for child in node.children:check_methods(child)
        check_methods(parser.parse(data).root_node)
    if original_method_hashes!=partition_method_hashes:raise ValueError('A helper or assertion body changed during partition')
    old['acceptance']=[t for t in original['acceptance'] if t.rsplit('.',1)[1] not in moved_names]
    note=primary.removesuffix('.cs')+'.repair-v39.md';guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    old['instructions']='Author only the five mapped Chat presentation/avatar methods and maintain owned shared Chat observation/input helpers. Read chat-authoring.v39.md and the approved user self-avatar override. All eighteen prior method bodies were preserved before this delegation. Strengthen every mapped source clause, fix the actual input-event compilation defect and invalid oracles, consolidate effective companion checks into mapped methods, and preserve genuine prior assertions. Expected failing tests against nonfunctional real services are required TDD, not business implementation. Actual current findings (only your mapped methods and owned helpers): '+finding+' Write '+note+' and its meta fileFormatVersion: 2 newline guid: '+guid+' newline as a truthful five-method clause map. Other focused partials and transferred notes are read-only. Return complete owned source through the bounded full-file protocol; never manufacture outcomes in recording adapters.'
    message_unit,state_unit=new_units
    message_unit['depends_on']=list(original['depends_on'])
    old['depends_on']=list(dict.fromkeys(original['depends_on']+['TEST-CHAT-MSG']))
    index=current['units'].index(old)
    current['units'][index:index+1]=[message_unit,old,state_unit]
    old['instructions']+=' ChatFocusInput is an exclusive message helper now owned by TEST-CHAT-MSG; do not edit that read-only helper. The message author runs first to repair its compilation defect.'
    world_path=source/'Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs';text=world_path.read_text(encoding='utf-8')
    marker='        public Action<string, string, string> NotificationEmitted;'
    if text.count(marker)!=1 or 'ChatDeliveryAllowed' in text:raise ValueError('Prepared delivery shape changed')
    world_path.write_text(text.replace(marker,marker+'\n        public Func<LobbyMessage, bool> ChatDeliveryAllowed;'),encoding='utf-8',newline='')
    spec=source/'specs/monopoly-game-lobby'
    (spec/'chat-authoring.v39.md').write_bytes(Path(__file__).with_name('chat-authoring.v39.md').read_bytes())
    acceptance=json.loads((spec/'acceptance-conditions.v16.json').read_bytes())
    for row in acceptance:
        if row['test'].endswith('Story_L13_03'):
            row['approved_user_override']='Player avatar is visible beside own right-aligned messages, per explicit user decision and approved proposal/spec. The original no-self-avatar source sentence is retained as provenance but is superseded.'
    (spec/'acceptance-conditions.v39.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    for unit in current['units']:
        if unit['id'] in ('SOCIAL','SHELL'):unit['instructions']+=' Read chat-authoring.v39.md. Implement the declared optional fake delivery gate, real pending send state and failure-preserved draft. Own avatars remain visible by explicit user override; original source exclusion is superseded.'
    (spec/'author-partitions.v39.json').write_text(json.dumps({'source_sha256':sha256(raw).hexdigest(),'all_eighteen_method_bodies_byte_identical':True,'all_method_bodies_byte_identical':True,'all_method_count':len(all_nodes),'helper_partition':'Only exclusively reachable helpers move; shared and unreachable helpers remain in the primary. Names conservatively include method-group references.','mapped_counts':[len(old['acceptance'])]+[len(u['acceptance']) for u in new_units],'parts':proofs,'rationale':rationale},indent=2)+'\n',encoding='utf-8',newline='')
    if [len(old['acceptance'])]+[len(u['acceptance']) for u in new_units]!=[5,4,5]:
        raise ValueError('Mapped partition counts changed')
    for unit in (old,*new_units):
        unit['instructions']+=' The explicit user self-avatar override in chat-authoring.v39.md supersedes the contrary sentence repeated in the dossier. Return complete owned source through the guarded full-file transport.'
    profile=json.loads((source/current['coding_profile_ref']['path']).read_bytes())
    for reference in profile['rules']:
        if reference['path']=='Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs':
            reference['sha256']=sha256(world_path.read_bytes()).hexdigest()
    profile['protected_paths'] += [p+'.meta' for p,_,_ in parts.values()]
    path='specs/monopoly-game-lobby/coding-profile.chat-v39.json'
    (source/path).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    current['coding_profile_ref']={'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
