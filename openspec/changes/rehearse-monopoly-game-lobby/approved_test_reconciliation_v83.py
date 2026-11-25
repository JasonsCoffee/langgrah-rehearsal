"""Guard the four explicitly approved Cards method bodies."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='a6a9fcd7db0dad8145e14ac6c644c90c0a477af2e86821bc7189dfef1aed249a'
REPLY='Ok, method changes are approved. At the same time, increase the input ceiling to 70M. Please continue.'
SCOPE={'TEST-CARDS':{'path':'Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyRechargeTests.cs',
                     'methods':['RoleAssociatedAmount','IsMeasurableGraphicForCards',
                                'IsRenderedLabelForCards','Story_L12_05']}}


def author_paths(unit: str) -> tuple[str,...]:
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-CARDS.reconciliation-v83.md'
    return SCOPE[unit]['path'],note,note+'.meta'


def cards_first(units: list[dict]) -> list[dict]:
    order=('TEST-CARDS','TEST-HARNESS','TEST-APPEAR','TEST-VIP')
    by_id={unit['id']:unit for unit in units}
    return [*(by_id[unit] for unit in order),*(unit for unit in units if unit['id'] not in order)]


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    path=SCOPE[unit]['path']
    if path not in patch or set(patch)-set(author_paths(unit)):
        raise ValueError('Only approved method bodies and owned provenance notes may change')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Unit count changed')
    for previous,current in zip(cards_first(old['units']),new['units']):
        expected=dict(previous)
        if previous['id']=='TEST-CARDS':
            expected.update(owns=previous['owns']+list(author_paths('TEST-CARDS')[1:]),instructions=current['instructions'])
        if current!=expected:raise ValueError('Unapproved unit, acceptance or ownership change')
    if new!=old|{'contract_version':83,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def retained_hashes(state: Path,source: Path,candidate: str) -> dict[str,str]:
    from approved_test_reconciliation_v79 import author_paths as paths79
    from approved_test_reconciliation_v82 import author_paths as paths82
    from frozen_budget_continuation import protected_tests
    from unity_coder.core.workspaces import git

    run=state/'.agent/runs/monopoly-game-lobby'
    prior=json.loads((run/'services-v82/state.json').read_bytes())
    if prior['candidate_revision']!=candidate or 'TEST-VIP' not in prior['tdd']['reviews']:
        raise ValueError('Retaining VIP requires its independently reviewed candidate')
    manifest=json.loads((state/'frozen-continuations/v82.json').read_bytes())
    checked=protected_tests(state,state.parent/'worktrees/architect-v82',82)
    frozen={path:manifest['frozen'][path] for path in checked}
    for path in set(paths79('TEST-VIP')+paths82('TEST-VIP')):
        frozen[path]=sha256(git(source,'show',candidate+':'+path)).hexdigest()
    return frozen


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources

    run=state/'.agent/runs/monopoly-game-lobby'
    approval=json.loads((state/'model-authorizations/test-reconciliation-v83.json').read_bytes())
    previous=(run/'cycles/v82/result.json').read_bytes()
    dossier=(run/'dossier-v82.json').read_bytes()
    transition=json.loads((run/'transitions/v83.json').read_bytes())
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v82.json').read_bytes()
    new=(spec/'contract.v83.json').read_bytes()
    if (version!=83 or manifest['version']!=83 or manifest['scope']!=SCOPE
        or approval!={'authority':'explicit_user_session','reply':REPLY,'version':83,'scope':SCOPE}
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Cards approval or transition identity changed')
    validate_revision(json.loads(old),json.loads(new))
    expected=retained_hashes(state,source,json.loads(previous)['candidate_revision'])
    if manifest['frozen']!=expected:
        raise ValueError('Prior reviewed and unaffected test bytes changed')
    return check_frozen_sources(source,{path:digest for path,digest in expected.items()
                                        if path!=SCOPE['TEST-CARDS']['path']})
