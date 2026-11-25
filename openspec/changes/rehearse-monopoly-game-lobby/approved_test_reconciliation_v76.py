"""Carry approved NFR and Appearance work and finish the authorized Chat repair."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='780598d1efcc59251207688be4610f221bb284756fa95a7230b4f201804731b9'
from approved_test_reconciliation_v75 import SCOPE as PRIOR_SCOPE, author_paths as prior_paths
from approved_test_reconciliation_v73 import CHAT, REPLY

SCOPE=PRIOR_SCOPE|{'TEST-CHAT-MSG':CHAT}


def author_paths(unit: str) -> tuple[str,...]:
    if unit in PRIOR_SCOPE:
        return prior_paths(unit)
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-CHAT-MSG.exact-avatar-v76.md'
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
    if new!=old|{'contract_version':76,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources, protected_tests
    run=state/'.agent/runs/monopoly-game-lobby'
    approval=json.loads((state/'model-authorizations/test-reconciliation-v73.json').read_bytes())
    previous=(run/'cycles/v75/result.json').read_bytes()
    dossier=(run/'dossier-v75.json').read_bytes()
    transition=json.loads((run/'transitions/v76.json').read_bytes())
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v75.json').read_bytes()
    new=(spec/'contract.v76.json').read_bytes()
    if (version!=76 or manifest['version']!=76 or manifest['scope']!=SCOPE
        or approval!={'authority':'explicit_user_session','reply':REPLY,'version':73,'scope':{'TEST-CHAT-MSG':CHAT}}
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or manifest['dossier_sha256']!=sha256(dossier).hexdigest()
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Carried Chat approval or transition identity changed')
    validate_revision(json.loads(old),json.loads(new))
    protected_tests(state,state.parent/'worktrees/architect-v75',75)
    expected=json.loads((state/'frozen-continuations/v75.json').read_bytes())['frozen']
    if manifest['frozen']!=expected:
        raise ValueError('Prior frozen test inventory changed')
    writable={entry['path'] for entry in SCOPE.values()}
    return check_frozen_sources(source,{path:digest for path,digest in expected.items() if path not in writable})
