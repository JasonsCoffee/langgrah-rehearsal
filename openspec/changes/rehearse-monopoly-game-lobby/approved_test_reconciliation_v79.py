"""Guard the two explicitly approved VIP rule helpers."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='d89225b3ef7850527c8dbb0df9bc4c4c1def0010a7eb087f8025b792fd756606'
REPLY='Ok, approved.'
SCOPE={'TEST-VIP':{'path':'Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyVipTests.cs',
                   'methods':['AssertRulesRowsForLevels','ContainsDistinctAmountField']}}


def author_paths(unit: str) -> tuple[str,...]:
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-VIP.reconciliation-v79.md'
    return SCOPE[unit]['path'],note,note+'.meta'


def vip_first(units: list[dict]) -> list[dict]:
    order=['TEST-HARNESS','TEST-APPEAR','TEST-CARDS','TEST-VIP']
    by_id={unit['id']:unit for unit in units}
    for index,unit_id in enumerate(order):
        if not set(by_id[unit_id]['depends_on'])<=set(order[:index]):
            raise ValueError('VIP preparation order would move an unmet dependency')
    return [*(by_id[unit_id] for unit_id in order),*(unit for unit in units if unit['id'] not in order)]


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    path=SCOPE[unit]['path']
    if path not in patch or set(patch)-set(author_paths(unit)):
        raise ValueError('Only approved method bodies and owned provenance notes may change')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Unit count changed')
    for previous,current in zip(vip_first(old['units']),new['units']):
        expected=dict(previous)
        if previous['id']=='TEST-VIP':
            expected.update(owns=previous['owns']+list(author_paths('TEST-VIP')[1:]),instructions=current['instructions'])
        if current!=expected:raise ValueError('Unapproved unit, acceptance or ownership change')
    if new!=old|{'contract_version':79,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def retained_hashes(state: Path,source: Path,candidate: str) -> dict[str,str]:
    from approved_test_reconciliation_v76 import SCOPE as prior_scope, author_paths as prior_paths
    from frozen_budget_continuation import protected_tests
    from unity_coder.core.workspaces import git

    run=state/'.agent/runs/monopoly-game-lobby'
    prior=json.loads((run/'services-v78/state.json').read_bytes())
    if prior['candidate_revision']!=candidate or not set(prior_scope)<=prior['tdd']['reviews'].keys():
        raise ValueError('Retaining prior changes requires their independently reviewed candidate')
    manifest=json.loads((state/'frozen-continuations/v78.json').read_bytes())
    checked=protected_tests(state,state.parent/'worktrees/architect-v78',78)
    frozen={path:manifest['frozen'][path] for path in checked}
    for unit_id in prior_scope:
        for path in prior_paths(unit_id):
            frozen[path]=sha256(git(source,'show',candidate+':'+path)).hexdigest()
    return frozen


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources

    run=state/'.agent/runs/monopoly-game-lobby'
    approval=json.loads((state/'model-authorizations/test-reconciliation-v79.json').read_bytes())
    previous=(run/'cycles/v78/result.json').read_bytes()
    dossier=(run/'dossier-v78.json').read_bytes()
    transition=json.loads((run/'transitions/v79.json').read_bytes())
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v78.json').read_bytes()
    new=(spec/'contract.v79.json').read_bytes()
    if (version!=79 or manifest['version']!=79 or manifest['scope']!=SCOPE
        or approval!={'authority':'explicit_user_session','reply':REPLY,'version':79,'scope':SCOPE}
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('VIP approval or transition identity changed')
    validate_revision(json.loads(old),json.loads(new))
    expected=retained_hashes(state,source,json.loads(previous)['candidate_revision'])
    if manifest['frozen']!=expected:
        raise ValueError('Prior reviewed and unaffected test bytes changed')
    return check_frozen_sources(source,{path:digest for path,digest in expected.items()
                                        if path!=SCOPE['TEST-VIP']['path']})

def vip_before_cards_review(units: list[dict]) -> list[dict]:
    """Use the already-authored Cards source while prioritizing VIP review."""
    index=next(i for i,unit in enumerate(units) if unit['id']=='TEST-CARDS')
    if units[index+1]['id']!='TEST-VIP':
        raise ValueError('Expected the exact previous Cards/VIP preparation order')
    return [*units[:index],units[index+1],units[index],*units[index+2:]]


def protect_review_order(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_contract_continuity

    run=state/'.agent/runs/monopoly-game-lobby'
    previous=(run/'cycles/v79/result.json').read_bytes()
    transition=json.loads((run/'transitions/v80.json').read_bytes())
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v79.json').read_bytes()
    new=(spec/'contract.v80.json').read_bytes()
    prior_manifest=json.loads((state/'frozen-continuations/v79.json').read_bytes())
    if (version!=80 or manifest['version']!=80 or manifest['scope']!=SCOPE
        or manifest['frozen']!=prior_manifest['frozen']
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or json.loads(previous)['contract_sha256']!=sha256(old).hexdigest()
        or transition['state']!='complete' or transition['previous_sha256']!=sha256(old).hexdigest()
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Prior VIP authority and candidate must remain intact')
    old_contract=json.loads(old)
    old_contract['units']=vip_before_cards_review(old_contract['units'])
    check_contract_continuity(old_contract,json.loads(new),sha256(old).hexdigest())
    return protect(state,source,79,prior_manifest)
