"""Guard only the approved Appearance corrections."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='80633a01b3edf2c72c6aefac09c960d08b024756ec51af748f7372ee60e0402a'
REPLY='Approve these two Appearance corrections'
SCOPE={'TEST-APPEAR':{'path':'Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyTests.cs',
                      'methods':['AssertVisibleThumbnail','Journey_ECON']}}


def author_paths(unit: str) -> tuple[str,...]:
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-APPEAR.reconciliation-v74.md'
    return SCOPE[unit]['path'],note,note+'.meta'


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    path=SCOPE[unit]['path']
    if path not in patch or set(patch)-set(author_paths(unit)):
        raise ValueError('Only approved method bodies and owned provenance notes may change')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Unit count changed')
    for previous,current in zip(old['units'],new['units']):
        expected=dict(previous)
        if previous['id']=='TEST-APPEAR':
            expected.update(owns=previous['owns']+list(author_paths('TEST-APPEAR')[1:]),instructions=current['instructions'])
        if current!=expected:raise ValueError('Unapproved unit, acceptance or ownership change')
    if new!=old|{'contract_version':74,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources
    from unity_coder.core.workspaces import git

    run=state/'.agent/runs/monopoly-game-lobby'
    approval=json.loads((state/'model-authorizations/test-reconciliation-v74.json').read_bytes())
    previous=(run/'cycles/v73/result.json').read_bytes()
    dossier=(run/'dossier-v73.json').read_bytes()
    transition=json.loads((run/'transitions/v74.json').read_bytes())
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v73.json').read_bytes()
    new=(spec/'contract.v74.json').read_bytes()
    if (version!=74 or manifest['version']!=74 or manifest['scope']!=SCOPE
        or approval!={'authority':'explicit_user_session','reply':REPLY,'version':74,'scope':SCOPE}
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Appearance approval or transition identity changed')
    validate_revision(json.loads(old),json.loads(new))
    prior_manifest=json.loads((state/'frozen-continuations/v73.json').read_bytes())
    expected=retained_hashes(source,json.loads(previous)['candidate_revision'],prior_manifest)
    if manifest['frozen']!=expected:
        raise ValueError('Prior approved or unaffected test bytes changed')
    return check_frozen_sources(source,{path:digest for path,digest in expected.items()
                                        if path!=SCOPE['TEST-APPEAR']['path']})


def retained_hashes(source: Path,candidate: str,previous: dict) -> dict[str,str]:
    from approved_test_reconciliation_v73 import author_paths as prior_paths
    from unity_coder.core.workspaces import git

    frozen=dict(previous['frozen'])
    for unit in previous['scope']:
        for path in prior_paths(unit):
            frozen[path]=sha256(git(source,'show',candidate+':'+path)).hexdigest()
    return frozen
