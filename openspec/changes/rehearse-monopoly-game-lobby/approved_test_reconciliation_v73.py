"""Extend the existing two-method scope by two explicitly approved Chat helpers."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change
from approved_test_reconciliation_v71 import SCOPE as PREVIOUS_SCOPE,author_paths as previous_paths

PREVIOUS_SHA='0b01690d1de8bc3761495291d566da4d4cf0da20d85be0e6106c56e13a43b242'
REPLY='Approve these two helper corrections'
CHAT={'path':'Tests/Runtime/Script/LobbyRehearsal/LobbyChatMessageTests.cs',
      'methods':['MsgAvatarSpritesForRow','MsgPermittedRowGraphics']}
SCOPE=PREVIOUS_SCOPE|{'TEST-CHAT-MSG':CHAT}


def author_paths(unit: str) -> tuple[str,...]:
    if unit in PREVIOUS_SCOPE:return previous_paths(unit)
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-CHAT-MSG.reconciliation-v73.md'
    return CHAT['path'],note,note+'.meta'


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    path=SCOPE[unit]['path']
    if path not in patch or set(patch)-set(author_paths(unit)):
        raise ValueError('Only approved method bodies and owned provenance notes may change')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Unit count changed')
    for previous,current in zip(old['units'],new['units']):
        expected=dict(previous)
        if previous['id']=='TEST-CHAT-MSG':
            expected.update(owns=previous['owns']+list(author_paths('TEST-CHAT-MSG')[1:]),instructions=current['instructions'])
        if current!=expected:raise ValueError('Unapproved unit, acceptance or ownership change')
    if new!=old|{'contract_version':73,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources
    run=state/'.agent/runs/monopoly-game-lobby'
    approval=json.loads((state/'model-authorizations/test-reconciliation-v73.json').read_bytes())
    old_approval=(state/'model-authorizations/test-reconciliation-v71.json').read_bytes()
    previous=(state/'frozen-continuations/v72.json').read_bytes()
    prior=(run/'services-v72/state.json').read_bytes()
    result=(run/'cycles/v72/result.json').read_bytes()
    dossier=(run/'dossier-v72.json').read_bytes()
    frozen=json.loads((state/'frozen-continuations/v71.json').read_bytes())['frozen']
    old=(source/'specs/monopoly-game-lobby/contract.v72.json').read_bytes()
    new=(source/'specs/monopoly-game-lobby/contract.v73.json').read_bytes()
    transition=json.loads((run/'transitions/v73.json').read_bytes())
    if (version!=73 or manifest['version']!=73 or manifest['scope']!=SCOPE
        or approval!={'authority':'explicit_user_session','reply':REPLY,'version':73,'scope':{'TEST-CHAT-MSG':CHAT}}
        or json.loads(old_approval).get('reply')!='Approve both scoped corrections'
        or manifest['previous_approval_sha256']!=sha256(old_approval).hexdigest()
        or manifest['previous_manifest_sha256']!=sha256(previous).hexdigest()
        or manifest['previous_services_sha256']!=sha256(prior).hexdigest()
        or manifest['previous_result_sha256']!=sha256(result).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or json.loads(result)['outcome']!='rework' or json.loads(result)['contract_version']!=72
        or manifest['frozen']!=frozen or json.loads(previous)['frozen']!=frozen or len(frozen)!=199
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Scoped Chat approval lost exact authority or frozen/native history')
    validate_revision(json.loads(old),json.loads(new))
    writable={s['path'] for s in SCOPE.values()}
    return check_frozen_sources(source,{p:h for p,h in frozen.items() if p not in writable})
