"""Explicit, method-bounded test revision after the real cycle-67 dossier."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_c_sharp

PREVIOUS_SHA='013c774cf990ebacc14e4cb4fcbddf954bb3aadb5ce2abfdd9885d7dc29e3783'
REPLY='Ok, your request to change the frozen tests is approved.'
ROOT='Tests/Runtime/Script/LobbyRehearsal/'
SCOPE={
    'TEST-HARNESS':{'path':ROOT+'LobbyHarness.cs','methods':['PreparedAssetsAreInspectable']},
    'TEST-PRES-CORE':{'path':ROOT+'LobbyPresentationCoreTests.cs','methods':['Story_L1_05']},
    'TEST-PRES-NFR':{'path':ROOT+'LobbyPresentationNfrTests.cs','methods':['Story_NFR_03']},
}


def validate_authority(approval: dict,result: dict,dossier: dict) -> None:
    if (approval!={'authority':'explicit_user_session','reply':REPLY,'version':68,'scope':SCOPE}
        or result.get('outcome')!='rework' or result.get('contract_version')!=67
        or result.get('contract_sha256')!=PREVIOUS_SHA
        or dossier.get('contract_version')!=67 or dossier.get('contract_sha256')!=PREVIOUS_SHA
        or not any(u.get('id')=='SHELL' and u.get('defect_class')=='contract' for u in dossier.get('failed_units',[]))):
        raise ValueError('Explicit scoped user approval and actual contract rework required')


def validate_method_change(before: bytes,after: bytes,methods: tuple[str,...]) -> None:
    """Retain every byte outside approved bodies, including attributes/signatures."""
    parser=Parser(Language(tree_sitter_c_sharp.language()))
    def mask(raw: bytes) -> bytes:
        tree=parser.parse(raw)
        if tree.root_node.has_error:raise ValueError('Invalid C# cannot enter test reconciliation')
        blocks=[];found=[]
        def visit(node) -> None:
            if node.type=='method_declaration':
                name=node.child_by_field_name('name');body=node.child_by_field_name('body')
                value=raw[name.start_byte:name.end_byte].decode() if name else ''
                if value in methods:
                    if body is None or body.type!='block':raise ValueError('Approved method body missing')
                    blocks.append((body.start_byte,body.end_byte,value));found.append(value)
            for child in node.children:visit(child)
        visit(tree.root_node)
        if sorted(found)!=sorted(methods):raise ValueError('Approved method identity missing or duplicated')
        result=raw
        for start,end,name in sorted(blocks,reverse=True):result=result[:start]+('APPROVED_BODY_'+name).encode()+result[end:]
        return result
    if before==after or mask(before)!=mask(after):raise ValueError('Test changes escaped approved method bodies')


def author_paths(unit: str) -> tuple[str,...]:
    item=SCOPE[unit];note=ROOT+unit+'.reconciliation-v68.md'
    return item['path'],note,note+'.meta'


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Reconciliation cannot change unit count')
    for previous,current in zip(old['units'],new['units']):
        expected=dict(previous)
        if previous['id'] in SCOPE:
            expected.update(owns=previous['owns']+list(author_paths(previous['id'])[1:]),instructions=current['instructions'])
        elif previous['role']=='impl':expected['instructions']=current['instructions']
        if current!=expected:raise ValueError('Reconciliation changed unrelated ownership or acceptance')
    expected=old|{'contract_version':68,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}
    if new!=expected:raise ValueError('Reconciliation changed protected contract scope')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources
    run=state/'.agent/runs/monopoly-game-lobby'
    previous=(run/'services-v67/state.json').read_bytes()
    result=(run/'cycles/v67/result.json').read_bytes();dossier=(run/'dossier-v67.json').read_bytes()
    approval=json.loads((state/'model-authorizations/test-reconciliation-v68.json').read_bytes())
    validate_authority(approval,json.loads(result),json.loads(dossier))
    old=(source/'specs/monopoly-game-lobby/contract.v67.json').read_bytes()
    current=(source/'specs/monopoly-game-lobby/contract.v68.json').read_bytes()
    validate_revision(json.loads(old),json.loads(current))
    transition=json.loads((run/'transitions/v68.json').read_bytes());frozen=json.loads(previous)['tdd']['frozen']
    if (version!=68 or manifest['version']!=68 or manifest['frozen']!=frozen or len(frozen)!=189
        or manifest['previous_services_sha256']!=sha256(previous).hexdigest()
        or manifest['previous_result_sha256']!=sha256(result).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(current).hexdigest()):
        raise ValueError('Approved reconciliation lost native transition or frozen history')
    writable={s['path'] for s in SCOPE.values()}
    retained={p:h for p,h in frozen.items() if p not in writable}
    return check_frozen_sources(source,retained)


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    allowed=author_paths(unit)
    if not patch or set(patch)-set(allowed):raise ValueError('Unapproved test-author write')
    path=SCOPE[unit]['path']
    if path not in patch:raise ValueError('The scoped assertion repair is missing')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))
