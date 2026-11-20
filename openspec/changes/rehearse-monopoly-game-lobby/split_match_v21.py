"""Byte-preserving fixture partition; no handwritten assertions or behavior."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from tree_sitter import Language, Parser
import tree_sitter_c_sharp


def prepare(source: Path, current: dict, dossier: dict) -> None:
    if current['contract_version'] != 21 or {u['id'] for u in dossier['failed_units']} != {'TEST-MATCH'}:
        raise ValueError('Only the actual exhausted matchmaking fixture may be split')
    parser = Parser(Language(tree_sitter_c_sharp.language()))

    def methods(data: bytes) -> dict:
        tree = parser.parse(data)
        if tree.root_node.has_error:
            raise ValueError('Only valid delegated syntax may be partitioned')
        found = {}
        def visit(node):
            if node.type == 'method_declaration' and any(c.type == 'attribute_list' and b'[Test]' in c.text for c in node.children):
                name = node.child_by_field_name('name').text.decode()
                if name in found:
                    raise ValueError('Duplicate mapped method')
                found[name] = (node.start_byte, node.end_byte, node.text)
            for child in node.children:
                visit(child)
        visit(tree.root_node)
        return found

    prefix = 'Tests/Runtime/Script/LobbyRehearsal/'
    primary = prefix+'LobbyMatchTests.cs'
    destinations = {'TEST-MATCH': primary, 'TEST-QUEUE': prefix+'LobbyMatchQueueTests.cs', 'TEST-PARTY': prefix+'LobbyMatchPartyTests.cs'}
    raw = (source / primary).read_bytes()
    before = methods(raw)
    if len(before) != 21:
        raise ValueError('Expected all twenty-one existing methods')
    def owner(name):
        return 'TEST-MATCH' if name.startswith('Story_L9_') else 'TEST-PARTY' if name.startswith('Story_L11_') else 'TEST-QUEUE'
    counts = {u: sum(owner(n) == u for n in before) for u in destinations}
    if counts != {'TEST-MATCH': 6, 'TEST-QUEUE': 8, 'TEST-PARTY': 7}:
        raise ValueError('Unexpected method grouping')
    root = parser.parse(raw).root_node
    usings = b'\n'.join(n.text for n in root.children if n.type == 'using_directive')
    base = raw
    for start, end, _ in sorted((v for n, v in before.items() if owner(n) != 'TEST-MATCH'), reverse=True):
        base = base[:start]+b'\n'+base[end:]
    marker = b'public sealed class LobbyMatchTests'
    if base.count(marker) != 1:
        raise ValueError('Unexpected fixture declaration')
    parts = {'TEST-MATCH': base.replace(marker, b'public sealed partial class LobbyMatchTests', 1)}
    for unit_id in ('TEST-QUEUE', 'TEST-PARTY'):
        parts[unit_id] = usings+b'\nnamespace jj.Monopoly.Tests.LobbyRehearsal\n{\n    public sealed partial class LobbyMatchTests\n    {\n'
        parts[unit_id] += b'\n\n'.join(v[2] for n, v in sorted(before.items()) if owner(n) == unit_id)+b'\n    }\n}\n'
    after = {}
    for part in parts.values():
        rows = methods(part)
        if set(after) & set(rows):
            raise ValueError('Split duplicated a method')
        after.update(rows)
    if set(after) != set(before) or any(after[n][2] != before[n][2] for n in before):
        raise ValueError('No assertion bytes may change during Architect partition')
    for unit_id, data in parts.items():
        path = destinations[unit_id]
        if unit_id != 'TEST-MATCH' and (source / path).exists():
            raise ValueError('Preserve existing partial sources')
        (source / path).write_bytes(data)
        if unit_id != 'TEST-MATCH':
            (source / (path+'.meta')).write_text('fileFormatVersion: 2\nguid: '+uuid5(NAMESPACE_URL, 'monopoly-game-lobby/'+path).hex+'\n', encoding='utf-8', newline='')
    old = next(u for u in current['units'] if u['id'] == 'TEST-MATCH')
    original = deepcopy(old)
    histories = {
        'TEST-QUEUE': [p for p in old['owns'] if '.recovery-v4.md' in p],
        'TEST-PARTY': [p for p in old['owns'] if p.endswith(('LobbyMatchTests.acceptance.md', 'LobbyMatchTests.acceptance.md.meta'))],
    }
    if any(len(v) != 2 for v in histories.values()):
        raise ValueError('Repair lineage requires explicit historical transfers')
    transferred = {p for paths in histories.values() for p in paths}
    old['owns'] = [p for p in old['owns'] if p not in transferred]
    units = {'TEST-MATCH': old}
    for unit_id in ('TEST-QUEUE', 'TEST-PARTY'):
        units[unit_id] = dict(id=unit_id, role='test', status='active', title='Focused '+unit_id.lower()+' acceptance', spec_ref='LOBBY', owns=[destinations[unit_id]]+histories[unit_id], acceptance=[], depends_on=['TEST-HARNESS', 'TEST-MATCH'], interfaces=[], add_justification='Three reviews of twenty-one combined matchmaking tests left distinct tier, queue and party UI/race defects. Partition the same source into six, eight and seven byte-identical methods with explicit inherited history; preserve all selected IDs and assertions.')
    finding = dossier['failed_units'][0]['hypothesis']
    for unit_id, unit in units.items():
        unit['acceptance'] = [test for test in original['acceptance'] if owner(test.rsplit('.', 1)[1]) == unit_id]
        note = destinations[unit_id].removesuffix('.cs')+'.focused-v21.md'
        unit['owns'] += [note, note+'.meta']
        guid = uuid5(NAMESPACE_URL, 'monopoly-game-lobby/'+note).hex
        inherited_new_note = primary.removesuffix('.cs')+'.repair-v21.md'
        extra = (' Also write '+inherited_new_note+' and its meta with guid '+uuid5(NAMESPACE_URL, 'monopoly-game-lobby/'+inherited_new_note).hex+'.') if unit_id == 'TEST-MATCH' else ''
        unit['instructions'] = ('Repair only the mapped '+str(counts[unit_id])+' methods in your owned partial LobbyMatchTests file. All twenty-one bodies were mechanically preserved byte-for-byte; preserve every effective assertion and exact test ID. Shared helpers remain in LobbyMatchTests.cs, owned by TEST-MATCH; other authors receive them read-only and may add distinct private helpers in their own partial. Tests have NEVER globally frozen. Latest actual independent findings, apply the clauses assigned to you: '+finding+' Use real bound-view serialized button/drag/scroll interactions, supplied framework preference APIs and independent fixtures; never manufacture business outcomes in recording ports. Expected service-shell failures are behavioral Red, not setup null dereferences. Use hash-bound edits, not full C# replacement. Write '+note+' with a truthful clause-level map for your mapped tests, and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Preserve transferred historical notes unchanged.'+extra+' No handwritten game behavior. All source remains subject to the independent judge and actual Unity compilation.')
    index = current['units'].index(old)+1
    current['units'][index:index] = [units['TEST-QUEUE'], units['TEST-PARTY']]
    current['ownership_migrations'] = [dict(from_unit='TEST-MATCH', to_unit=u, paths=paths, rationale='Retain inherited repair lineage during byte-preserving fixture partition.') for u, paths in histories.items()]
    for link in current['test_links']:
        if link['author_unit'] == 'TEST-MATCH':
            link['author_unit'] = owner(link['test_id'].rsplit('.', 1)[1])
    for link in current['task_links']:
        if 'TEST-MATCH' in link['unit_ids']:
            link['unit_ids'] += ['TEST-QUEUE', 'TEST-PARTY']
    spec = source / 'specs/monopoly-game-lobby'
    world_path='Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs'
    raw_world=(source/world_path).read_bytes()
    marker=b'        public Func<string, LobbyVip> PlatformVipSnapshot;'
    if raw_world.count(marker)!=1:
        raise ValueError('Unexpected fake result API baseline')
    newline=b'\r\n' if b'\r\n' in raw_world else b'\n'
    (source/world_path).write_bytes(raw_world.replace(marker,marker+newline+b'        public Func<string, string, LobbyMatchRecord> MatchCompletionSnapshot;'))
    guide='specs/monopoly-game-lobby/completion-fixture.v21.md'
    (source/guide).write_bytes(Path(__file__).with_name('completion-fixture.v21.md').read_bytes())
    for unit in current['units']:
        if unit['id'] in ('TEST-QUEUE','MATCH'):
            unit['instructions']+=' Read completion-fixture.v21.md and the nonfunctional MatchCompletionSnapshot declaration. Arrange distinct result DTOs before completion and assert exact projection and durable idempotency independently of post-completion output; all service behavior remains delegated.'
    evidence = {'original_source_sha256': sha256(raw).hexdigest(), 'method_sha256': {n: sha256(v[2]).hexdigest() for n, v in before.items()}, 'destination': {n: destinations[owner(n)] for n in before}, 'all_21_method_bodies_byte_identical': True, 'counts': counts}
    (spec / 'match-source-split.v21.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8', newline='')
    profile = json.loads((source / current['coding_profile_ref']['path']).read_bytes())
    def ref(path):
        return {'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
    profile['rules']=[ref(row['path']) if row['path']==world_path else row for row in profile['rules']]
    profile['rules'].append(ref(guide));profile['protected_paths'].append(guide)
    profile['protected_paths'] += [destinations[u]+'.meta' for u in ('TEST-QUEUE', 'TEST-PARTY')]
    path = 'specs/monopoly-game-lobby/coding-profile.v21.json'
    (source / path).write_text(json.dumps(profile, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='')
    current['coding_profile_ref'] = {'path': path, 'sha256': sha256((source / path).read_bytes()).hexdigest()}
    presentation=json.loads((source/current['presentation_ref']['path']).read_bytes())
    presentation['files']=[ref(row['path']) if row['path']==world_path else row for row in presentation['files']]
    presentation_path='specs/monopoly-game-lobby/presentation.v21.json'
    (source/presentation_path).write_text(json.dumps(presentation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
    current['presentation_ref']=ref(presentation_path)
