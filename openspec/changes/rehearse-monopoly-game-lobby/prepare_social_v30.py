"""Byte-preserving test partition and nonfunctional fake-platform inputs."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from uuid import NAMESPACE_URL,uuid5
from tree_sitter import Language,Parser
import tree_sitter_c_sharp


def prepare(source: Path,current: dict,dossier: dict) -> None:
    if current['contract_version']!=30 or {u['id'] for u in dossier['failed_units']}!={'TEST-SOCIAL'}:
        raise ValueError('Only the inspected social-source rework may be prepared')
    parser=Parser(Language(tree_sitter_c_sharp.language()))
    prefix='Tests/Runtime/Script/LobbyRehearsal/';primary=prefix+'LobbySocialTests.cs'
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
    if set(before)!={'Story_L4_'+str(n).zfill(2) for n in range(1,20)}:raise ValueError('Expected all nineteen delegated friend tests')
    old=next(u for u in current['units'] if u['id']=='TEST-SOCIAL');original=deepcopy(old)
    parts={
        'TEST-FRIEND-REQUESTS':(prefix+'LobbySocialRequestsTests.cs',set(range(15,20)),'.focused-v23.md'),
        'TEST-PARTNER-RECS':(prefix+'LobbySocialPartnersTests.cs',set(range(11,15)),'.acceptance.md'),
    }
    usings=b'\n'.join(n.text for n in tree.root_node.children if n.type=='using_directive')
    base=raw;proofs=[];new_units=[];moved_names=set()
    finding=dossier['failed_units'][0]['hypothesis']
    rationale='The actual nineteen-method author exhausted three independent reviews across distinct friend UI, platform request and match-derived recommendation defects. Narrow responsibility without changing any assertion bytes; preserve inherited repair history and all mapped IDs.'
    for unit_id,(path,numbers,history_suffix) in parts.items():
        selected={n:v for n,v in before.items() if int(n.rsplit('_',1)[1]) in numbers};moved_names.update(selected)
        data=usings+b'\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed partial class LobbySocialTests\n    {\n'+b'\n\n'.join(v[2] for v in selected.values())+b'\n    }\n}\n'
        if (source/path).exists():raise ValueError('Preserve existing partial')
        (source/path).write_bytes(data)
        (source/(path+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+path).hex+'\n',encoding='utf-8',newline='')
        history=[p for p in original['owns'] if p.endswith(history_suffix) or p.endswith(history_suffix+'.meta')]
        if len(history)!=2 or any(not (source/p).exists() for p in history):raise ValueError('Existing history pair required for inherited lineage')
        old['owns']=[p for p in old['owns'] if p not in history]
        acceptance=[t for t in original['acceptance'] if t.rsplit('.',1)[1] in selected]
        note=path.removesuffix('.cs')+'.focused-v30.md';guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
        unit=dict(id=unit_id,role='test',status='active',title='Focused '+unit_id.lower()+' acceptance',spec_ref='LOBBY',
            owns=[path]+history+[note,note+'.meta'],acceptance=acceptance,
            depends_on=list(dict.fromkeys(original['depends_on']+['TEST-SOCIAL'])),interfaces=[],add_justification=rationale,
            instructions='Author only your '+str(len(acceptance))+' mapped methods in the owned partial. Every existing method body is byte-identical to the previous delegated source. Shared private helpers in other partials are read-only. Preserve every effective assertion and all source clauses; repair only findings relevant to your mapped methods. Read platform-inputs.v30.md. Historical transferred notes stay byte-identical. Current actual findings: '+finding+' Write '+note+' as a truthful current clause map and '+note+'.meta with fileFormatVersion: 2 newline guid: '+guid+' newline. Use the host hash-bound edit protocol, never game business implementation or conditional coverage bypasses.')
        new_units.append(unit)
        current['ownership_migrations'].append(dict(from_unit='TEST-SOCIAL',to_unit=unit_id,paths=history,rationale='Preserve inherited repair lineage while narrowing test authorship; no assertion edits.'))
        for link in current['test_links']:
            if link['author_unit']=='TEST-SOCIAL' and link['test_id'].rsplit('.',1)[1] in selected:link['author_unit']=unit_id
        for link in current['task_links']:
            if 'TEST-SOCIAL' in link['unit_ids']:link['unit_ids'].append(unit_id)
        proofs.append({'unit':unit_id,'path':path,'methods':list(selected),'method_sha256':{n:sha256(v[2]).hexdigest() for n,v in selected.items()},'transferred_history_sha256':{p:sha256((source/p).read_bytes()).hexdigest() for p in history}})
    for start,end,_ in sorted((v for n,v in before.items() if n in moved_names),reverse=True):base=base[:start]+b'\n'+base[end:]
    (source/primary).write_bytes(base)
    after=methods(base)
    for path,_,_ in parts.values():
        for name,value in methods((source/path).read_bytes()).items():
            if name in after:raise ValueError('Partition duplicated a method')
            after[name]=value
    if set(after)!=set(before) or any(after[n][2]!=v[2] for n,v in before.items()):raise ValueError('Partition changed an assertion body')
    old['acceptance']=[t for t in original['acceptance'] if t.rsplit('.',1)[1] not in moved_names]
    note=primary.removesuffix('.cs')+'.repair-v30.md';guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    old['instructions']='Author only the ten mapped friend-list/UI methods in your owned primary partial and maintain shared observation-only helpers. Read platform-inputs.v30.md. Every existing test body is preserved; all original clauses remain required. Implement your own pointer/raycast helpers using the supplied read-only presentation examples; private methods in another fixture class are not callable. Remove conditional command fallbacks for missing hit targets. Current actual findings (only your mapped clauses): '+finding+' Preserve transferred historical notes, which now belong to the focused authors. Write '+note+' and its meta with fileFormatVersion: 2 newline guid: '+guid+' newline as the truthful current ten-method clause map. No game business behavior or weakened assertions.'
    index=current['units'].index(old)+1
    current['units'][index:index]=new_units
    world_path=source/'Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs';text=world_path.read_text(encoding='utf-8')
    marker='        public Func<string, LobbyVip> PlatformVipSnapshot;'
    if text.count(marker)!=1 or 'PlatformAvatarOverride' in text:raise ValueError('Prepared provider shape changed')
    text=text.replace(marker,marker+'\n        public Func<string, UnityEngine.Sprite> PlatformAvatarOverride;\n        public int? PlatformFriendLimit;\n        public readonly System.Collections.Generic.Dictionary<string, System.Collections.Generic.HashSet<string>> PlatformFriends = new System.Collections.Generic.Dictionary<string, System.Collections.Generic.HashSet<string>>();\n        public bool PlatformRemoveFriendAllowed = true;')
    world_path.write_text(text,encoding='utf-8',newline='')
    spec=source/'specs/monopoly-game-lobby'
    guide=Path(__file__).with_name('platform-inputs.v30.md').read_bytes();(spec/'platform-inputs.v30.md').write_bytes(guide)
    for unit in current['units']:
        if unit['id'] in ('SOCIAL','SHELL','MATCH','RECORDS'):unit['instructions']+=' Read platform-inputs.v30.md for the nonfunctional fake-platform inputs and adversarial history fixtures. All behavior remains delegated; preserve the approved client/fake-service boundary and full-match deferral.'
    (spec/'author-partitions.v30.json').write_text(json.dumps({'source_sha256':sha256(raw).hexdigest(),'all_nineteen_method_bodies_byte_identical':True,'counts':[len(old['acceptance'])]+[len(u['acceptance']) for u in new_units],'parts':proofs,'rationale':rationale},indent=2)+'\n',encoding='utf-8',newline='')
    profile=json.loads((source/current['coding_profile_ref']['path']).read_bytes())
    for reference in profile['rules']:
        if reference['path']=='Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs':
            reference['sha256']=sha256(world_path.read_bytes()).hexdigest()
    profile['protected_paths'] += [p+'.meta' for p,_,_ in parts.values()]
    path='specs/monopoly-game-lobby/coding-profile.authors-v30.json'
    (source/path).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    current['coding_profile_ref']={'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
