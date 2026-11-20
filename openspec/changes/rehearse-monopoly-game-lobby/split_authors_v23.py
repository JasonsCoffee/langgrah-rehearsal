"""Partition acceptance authorship without changing a test method body."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from tree_sitter import Language, Parser
import tree_sitter_c_sharp


def prepare(source: Path, current: dict, dossier: dict) -> None:
    if current['contract_version'] != 23:
        raise ValueError('Only the reviewed consecutive boundary is supported')
    parser=Parser(Language(tree_sitter_c_sharp.language()))
    proofs=[]
    def split(old_id,new_id,primary,secondary,selected,existing_count,rationale):
        old=next(u for u in current['units'] if u['id']==old_id)
        original=deepcopy(old)
        raw=(source/primary).read_bytes();tree=parser.parse(raw)
        if tree.root_node.has_error:raise ValueError('Malformed delegated source cannot be partitioned')
        methods={}
        def visit(node):
            if node.type=='method_declaration' and any(c.type=='attribute_list' and b'[Test]' in c.text for c in node.children):
                name=node.child_by_field_name('name').text.decode()
                if name in methods:raise ValueError('Duplicate method')
                methods[name]=(node.start_byte,node.end_byte,node.text)
            for child in node.children:visit(child)
        visit(tree.root_node)
        if len(methods) not in ((existing_count,) if isinstance(existing_count,int) else existing_count):raise ValueError('Source inventory changed before partition')
        moved={n:v for n,v in methods.items() if selected(n)}
        moved_field=None
        if new_id=='TEST-VIP':
            fields=[]
            def find_field(node):
                if node.type=='field_declaration' and b'BaseVipBenefits' in node.text:fields.append(node)
                for child in node.children:find_field(child)
            find_field(tree.root_node)
            if len(fields)!=1:raise ValueError('Expected the shared VIP expectation data declaration')
            field=fields[0];moved_field=(field.start_byte,field.end_byte,field.text)
        base=raw
        spans=list(moved.values())+([moved_field] if moved_field else [])
        for start,end,_ in sorted(spans,reverse=True):base=base[:start]+b'\n'+base[end:]
        class_name='LobbyEconomyTests' if old_id=='TEST-CARDS' else 'LobbySocialTests'
        if old_id=='TEST-SOCIAL':
            marker=('public sealed class '+class_name).encode()
            if base.count(marker)!=1:raise ValueError('Unexpected social container')
            base=base.replace(marker,('public sealed partial class '+class_name).encode(),1)
        usings=b'\n'.join(n.text for n in tree.root_node.children if n.type=='using_directive')
        part=usings+b'\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed partial class '+class_name.encode()+b'\n    {\n'
        if moved_field:part+=moved_field[2]+b'\n'
        part+=b'\n\n'.join(v[2] for n,v in sorted(moved.items()))+b'\n    }\n}\n'
        if (source/secondary).exists():raise ValueError('Preserve existing partial')
        # Every original method is included verbatim in exactly one destination.
        for name,value in methods.items():
            dest=part if name in moved else base
            if dest.count(value[2])!=1:raise ValueError('A method body changed or duplicated')
        if parser.parse(base).root_node.has_error or parser.parse(part).root_node.has_error:raise ValueError('Split syntax invalid')
        (source/primary).write_bytes(base);(source/secondary).write_bytes(part)
        (source/(secondary+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+secondary).hex+'\n',encoding='utf-8',newline='')
        history=[p for p in old['owns'] if '.recovery-v4.md' in p]
        if len(history)!=2:raise ValueError('Explicit inherited history is required')
        transfer=list(history)
        if new_id=='TEST-VIP':transfer += [p for p in old['owns'] if '.catalog-consistency-v23.md' in p]
        old['owns']=[p for p in old['owns'] if p not in transfer]
        old['acceptance']=[t for t in original['acceptance'] if not selected(t.rsplit('.',1)[1])]
        new=dict(id=new_id,role='test',status='active',title='Focused '+new_id.lower()+' acceptance',spec_ref='LOBBY',owns=[secondary]+transfer,acceptance=[t for t in original['acceptance'] if selected(t.rsplit('.',1)[1])],depends_on=[old_id],interfaces=[],add_justification=rationale)
        new['depends_on']=list(dict.fromkeys(original['depends_on']+[old_id]))
        finding=' '.join(u['hypothesis'] for u in dossier['failed_units'] if u['id']==old_id)
        for unit,path in ((old,primary),(new,secondary)):
            note=path.removesuffix('.cs')+'.focused-v23.md';unit['owns'] += [note,note+'.meta']
            guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
            original_task=original['instructions'] if unit is old and old_id=='TEST-CARDS' else ''
            if ' Also repair the actual unsupported literal' in original_task:
                original_task=original_task.split(' Also repair the actual unsupported literal',1)[0]
            unit['instructions']=original_task+' Focus on only the '+str(len(unit['acceptance']))+' mapped methods in your owned partial. Existing bodies are byte-identical; preserve every effective assertion and exact ID. Shared private helpers in other partials are supplied read-only; declare distinct helpers in your owned partial if needed. All original source clauses and approved scope still apply. '+finding+' Write '+note+' as the current truthful clause-level acceptance map and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Historical transferred notes remain unchanged. Use hash-bound C# edits. Do not invent game business behavior in adapters or weaken assertions. This source requires real independent review and actual Unity compilation; no human acceptance is inferred.'
            if unit is old and old_id=='TEST-CARDS':
                (source/note).write_text('# Mechanical partition map\n\nThis Architect-generated mapping introduces no behavioral assertions or approval.\nThe existing delegated clause map remains at '+primary.removesuffix('.cs')+'.acceptance.md;\nonly the following retained methods belong to this partition. Every method body\nis byte-identical to the pre-partition source and remains independently reviewable.\n\n'+'\n'.join('- '+t for t in unit['acceptance'])+'\n',encoding='utf-8',newline='')
                (source/(note+'.meta')).write_text('fileFormatVersion: 2\nguid: '+guid+'\n',encoding='utf-8',newline='')
            for missing in unit['owns']:
                if missing.endswith('.md') and not (source/missing).exists():
                    unit['instructions']+=' Write the required new owned note '+missing+' and '+missing+'.meta with fileFormatVersion: 2 newline guid: '+uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+missing).hex+' newline.'
            if new_id=='TEST-VIP' and unit is new and any('.catalog-consistency-v23.md' in p for p in transfer):
                unit['instructions']+=' Apply architect-findings.v22.md: replace the unsupported discount literal with assertions of the actual prepared entry-benefit localization row, including a private sentinel proving its rendered data path; do not change catalog data. Write all owned catalog-consistency note/metadata files using the GUID supplied by the inherited observation task. '
                unit['instructions']+=original['instructions'].split(' Also repair the actual unsupported literal',1)[-1]
        current['units'].insert(current['units'].index(old)+1,new)
        current['ownership_migrations'].append(dict(from_unit=old_id,to_unit=new_id,paths=history,rationale='Preserve inherited repair history while narrowing authored source responsibility.'))
        for link in current['test_links']:
            if link['author_unit']==old_id and selected(link['test_id'].rsplit('.',1)[1]):link['author_unit']=new_id
        for link in current['task_links']:
            if old_id in link['unit_ids']:link['unit_ids'].append(new_id)
        proofs.append({'from_unit':old_id,'to_unit':new_id,'source_sha256':sha256(raw).hexdigest(),'existing_methods':len(methods),'moved_methods':len(moved),'all_existing_method_bodies_byte_identical':True,'method_sha256':{n:sha256(v[2]).hexdigest() for n,v in methods.items()},'planned_counts':[len(old['acceptance']),len(new['acceptance'])],'rationale':rationale})
    prefix='Tests/Runtime/Script/LobbyRehearsal/'
    split('TEST-CARDS','TEST-VIP',prefix+'LobbyEconomyRechargeTests.cs',prefix+'LobbyEconomyVipTests.cs',lambda n:n in {'Story_L12_06','Story_L12_07','Story_L12_08','Story_L12_09','Story_L12_11'},11,'Repeated real reviews of the combined eleven payment/VIP methods consumed several cycles with distinct transaction and rendering defects. Split six payment/card methods from five VIP/localization methods, preserving all assertion bytes and inherited history.')
    split('TEST-SOCIAL','TEST-CHAT',prefix+'LobbySocialTests.cs',prefix+'LobbySocialChatTests.cs',lambda n:n.startswith('Story_L13_') or n=='Journey_SOCIAL',(0,33),'The combined social author has thirty-three mapped methods. Based on observed repeated exhaustion of smaller mixed-domain fixtures, separate nineteen friend/recommendation methods from fourteen chat/journey methods within the bounded two-unit growth allowance. Preserve every existing assertion and leave all unimplemented assertions delegated; none is supplied by the Architect.')
    spec=source/'specs/monopoly-game-lobby';(spec/'author-partitions.v23.json').write_text(json.dumps(proofs,indent=2)+'\n',encoding='utf-8',newline='')
    profile=json.loads((source/current['coding_profile_ref']['path']).read_bytes())
    profile['protected_paths'] += [prefix+'LobbyEconomyVipTests.cs.meta',prefix+'LobbySocialChatTests.cs.meta']
    path='specs/monopoly-game-lobby/coding-profile.authors-v23.json'
    (source/path).write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    current['coding_profile_ref']={'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
