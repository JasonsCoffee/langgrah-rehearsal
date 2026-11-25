"""Guard approved NFR cleanup and the carried Appearance scope."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='8a5f4e4af2dded3f58b14d9a761cc618f8760b668a189ce49c087edf0fab25d1'
REPLY='ok, approved. continue the implementation.'
from approved_test_reconciliation_v74 import SCOPE as APPEARANCE, author_paths as appearance_paths

NFR={'TEST-PRES-NFR':{'path':'Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationNfrTests.cs',
                     'methods':[f'Story_NFR_0{i}' for i in range(1,5)]}}
SCOPE=APPEARANCE|NFR


def author_paths(unit: str) -> tuple[str,...]:
    if unit in APPEARANCE:
        return appearance_paths(unit)
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-PRES-NFR.cleanup-v75.md'
    return NFR[unit]['path'],note,note+'.meta'


def validate_patch(unit: str,patch: dict[str,bytes],source: Path) -> None:
    path=SCOPE[unit]['path']
    if path not in patch or set(patch)-set(author_paths(unit)):
        raise ValueError('Only approved method bodies and owned provenance notes may change')
    validate_method_change((source/path).read_bytes(),patch[path],tuple(SCOPE[unit]['methods']))


def validate_revision(old: dict,new: dict) -> None:
    if len(old['units'])!=len(new['units']):raise ValueError('Unit count changed')
    for previous,current in zip(old['units'],new['units']):
        expected=dict(previous)
        if previous['id']=='TEST-PRES-NFR':
            expected.update(owns=previous['owns']+list(author_paths('TEST-PRES-NFR')[1:]),instructions=current['instructions'])
        if current!=expected:raise ValueError('Unapproved unit, acceptance or ownership change')
    if new!=old|{'contract_version':75,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources
    from unity_coder.core.workspaces import git

    run=state/'.agent/runs/monopoly-game-lobby'
    approval=json.loads((state/'model-authorizations/test-reconciliation-v75.json').read_bytes())
    previous=(run/'cycles/v74/result.json').read_bytes()
    dossier=(run/'dossier-v74.json').read_bytes()
    transition=json.loads((run/'transitions/v75.json').read_bytes())
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v74.json').read_bytes()
    new=(spec/'contract.v75.json').read_bytes()
    if (version!=75 or manifest['version']!=75 or manifest['scope']!=SCOPE
        or approval!={'authority':'explicit_user_session','reply':REPLY,'version':75,'scope':NFR}
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Appearance approval or transition identity changed')
    validate_revision(json.loads(old),json.loads(new))
    prior_manifest=json.loads((state/'frozen-continuations/v74.json').read_bytes())
    prior_approval=json.loads((state/'model-authorizations/test-reconciliation-v74.json').read_bytes())
    from approved_test_reconciliation_v74 import REPLY as appearance_reply
    if prior_approval!={'authority':'explicit_user_session','reply':appearance_reply,'version':74,'scope':APPEARANCE}:
        raise ValueError('Original Appearance approval changed')
    expected=prior_manifest['frozen']
    if manifest['frozen']!=expected:
        raise ValueError('Prior frozen input inventory changed')
    writable={entry['path'] for entry in SCOPE.values()}
    return check_frozen_sources(source,{path:digest for path,digest in expected.items() if path not in writable})
