"""User-approved cycle-71 corrections remain confined to two test bodies."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='bbbfcf9dc2b51f1ffb9d8a935a1fbb72ca148ada5c2a89f6b37752065f9315e7'
REPLY='Approve both scoped corrections'
ROOT='Tests/Runtime/Script/LobbyRehearsal/'
PROFILE='specs/monopoly-game-lobby/coding-profile.v71.json'
PROTOCOL='specs/monopoly-game-lobby/binding-protocol.v71.md'
SCOPE={
    'TEST-PRES-CORE':{'path':ROOT+'LobbyPresentationCoreTests.cs','methods':['Story_L1_03']},
    'TEST-PRES-NFR':{'path':ROOT+'LobbyPresentationNfrTests.cs','methods':['Story_NFR_01']},
}


def author_paths(unit: str) -> tuple[str,...]:
    note=ROOT+unit+'.reconciliation-v71.md'
    return SCOPE[unit]['path'],note,note+'.meta'


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    path=SCOPE[unit]['path']
    if path not in patch or set(patch)-set(author_paths(unit)):
        raise ValueError('Only the approved test body and new provenance note may change')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Unit count changed')
    for previous,current in zip(old['units'],new['units']):
        expected=dict(previous)
        if previous['id'] in SCOPE:
            expected.update(owns=previous['owns']+list(author_paths(previous['id'])[1:]),instructions=current['instructions'])
        elif previous['role']=='impl':expected['instructions']=current['instructions']
        if current!=expected:raise ValueError('Unrelated ownership, acceptance or scheduling changed')
    expected=old|{'contract_version':71,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}
    if 'coding_profile_ref' in old:
        ref=new['coding_profile_ref']
        if ref.get('path')!=PROFILE or set(ref)!={'path','sha256'} or len(ref['sha256'])!=64:
            raise ValueError('Exact versioned profile reference required')
        expected['coding_profile_ref']=ref
    if new!=expected:raise ValueError('Protected contract scope changed')


def updated_profile(old: dict,protocol_hash: str) -> dict:
    result=json.loads(json.dumps(old))
    matches=[r for r in result['rules'] if r['path']=='specs/monopoly-game-lobby/binding-protocol.v2.md']
    if len(matches)!=1:raise ValueError('Exact previous binding rule required')
    matches[0].update(path=PROTOCOL,sha256=protocol_hash)
    result['protected_paths']+= [PROTOCOL,PROFILE]
    return result


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources
    run=state/'.agent/runs/monopoly-game-lobby'
    if version==72:
        previous_raw=(state/'frozen-continuations/v71.json').read_bytes()
        previous=json.loads(previous_raw)
        retained=protect(state,source,71,previous)
        old=(source/'specs/monopoly-game-lobby/contract.v71.json').read_bytes()
        current=json.loads((source/'specs/monopoly-game-lobby/contract.v72.json').read_bytes())
        result_raw=(run/'cycles/v71/result.json').read_bytes()
        prior_raw=(run/'services-v71/state.json').read_bytes()
        dossier_raw=(run/'dossier-v71.json').read_bytes()
        transition=json.loads((run/'transitions/v72.json').read_bytes())
        result=json.loads(result_raw)
        if (manifest['previous_manifest_sha256']!=sha256(previous_raw).hexdigest()
            or manifest['previous_result_sha256']!=sha256(result_raw).hexdigest()
            or manifest['previous_services_sha256']!=sha256(prior_raw).hexdigest()
            or manifest['dossier_sha256']!=sha256(dossier_raw).hexdigest()
            or manifest['frozen']!=previous['frozen'] or manifest['version']!=72
            or result['outcome']!='rework' or result['contract_version']!=71
            or current!=json.loads(old)|{'contract_version':72,'previous_contract_sha256':sha256(old).hexdigest()}
            or transition['state']!='complete' or transition['previous_sha256']!=sha256(old).hexdigest()
            or transition['next']['contract_sha256']!=sha256((source/'specs/monopoly-game-lobby/contract.v72.json').read_bytes()).hexdigest()):
            raise ValueError('Carried scoped approval lost exact native rework and frozen history')
        return retained
    prior_raw=(run/'services-v70/state.json').read_bytes()
    result_raw=(run/'cycles/v70/result.json').read_bytes()
    dossier_raw=(run/'dossier-v70.json').read_bytes()
    approval=json.loads((state/'model-authorizations/test-reconciliation-v71.json').read_bytes())
    frozen=json.loads(prior_raw)['tdd']['frozen']
    old=(source/'specs/monopoly-game-lobby/contract.v70.json').read_bytes()
    current=(source/'specs/monopoly-game-lobby/contract.v71.json').read_bytes()
    transition=json.loads((run/'transitions/v71.json').read_bytes())
    result=json.loads(result_raw)
    if (approval!={'authority':'explicit_user_session','reply':REPLY,'version':71,'scope':SCOPE}
        or result['outcome']!='rework' or result['contract_sha256']!=PREVIOUS_SHA
        or len(frozen)!=199 or frozen!=manifest['frozen']
        or version!=71 or manifest['version']!=71 or manifest['scope']!=SCOPE
        or manifest['previous_services_sha256']!=sha256(prior_raw).hexdigest()
        or manifest['previous_result_sha256']!=sha256(result_raw).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier_raw).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(current).hexdigest()):
        raise ValueError('Approved correction lost exact authority, transition or frozen history')
    validate_revision(json.loads(old),json.loads(current))
    old_contract=json.loads(old);new_contract=json.loads(current)
    original=(source/old_contract['coding_profile_ref']['path']).read_bytes()
    profile_raw=(source/PROFILE).read_bytes()
    protocol_old=(source/'specs/monopoly-game-lobby/binding-protocol.v2.md').read_bytes()
    protocol_new=(source/PROTOCOL).read_bytes()
    if (sha256(original).hexdigest()!=old_contract['coding_profile_ref']['sha256']
        or protocol_old.count(b'Friends, day ranking, history')!=1
        or protocol_new!=protocol_old.replace(b'Friends, day ranking, history',b'Friends, weekly ranking, history')
        or json.loads(profile_raw)!=updated_profile(json.loads(original),sha256(protocol_new).hexdigest())
        or sha256(profile_raw).hexdigest()!=new_contract['coding_profile_ref']['sha256']):
        raise ValueError('Versioned profile exceeded the approved binding-clause change')
    writable={s['path'] for s in SCOPE.values()}
    return check_frozen_sources(source,{p:h for p,h in frozen.items() if p not in writable})
