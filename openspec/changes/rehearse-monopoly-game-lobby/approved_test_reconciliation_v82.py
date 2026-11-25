"""Guard the two explicitly approved VIP rule helpers."""
from hashlib import sha256
import json
from pathlib import Path
from approved_test_reconciliation import validate_method_change

PREVIOUS_SHA='5a395b43b225d564f059ef0b6a3951780e99f59daaf2f7a28e2103d0b0755fd8'
SCOPE={'TEST-VIP':{'path':'Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyVipTests.cs',
                   'methods':['AssertRulesRowsForLevels','ContainsDistinctAmountField']}}


def author_paths(unit: str) -> tuple[str,...]:
    note='Tests/Runtime/Script/LobbyRehearsal/TEST-VIP.amount-field-v82.md'
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
        if previous['id']=='TEST-VIP':
            expected.update(owns=previous['owns']+list(author_paths('TEST-VIP')[1:]),instructions=current['instructions'])
        if current!=expected:raise ValueError('Unapproved unit, acceptance or ownership change')
    if new!=old|{'contract_version':82,'previous_contract_sha256':PREVIOUS_SHA,'units':new['units']}:
        raise ValueError('Protected contract scope changed')


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_frozen_sources, protected_tests

    run=state/'.agent/runs/monopoly-game-lobby'
    previous=(run/'cycles/v81/result.json').read_bytes()
    spec=source/'specs/monopoly-game-lobby'
    old=(spec/'contract.v81.json').read_bytes()
    new=(spec/'contract.v82.json').read_bytes()
    transition=json.loads((run/'transitions/v82.json').read_bytes())
    prior_manifest=json.loads((state/'frozen-continuations/v81.json').read_bytes())
    if (version!=82 or manifest['version']!=82 or manifest['scope']!=SCOPE
        or manifest['frozen']!=prior_manifest['frozen']
        or manifest['previous_result_sha256']!=sha256(previous).hexdigest()
        or json.loads(previous)['contract_sha256']!=PREVIOUS_SHA
        or sha256(old).hexdigest()!=PREVIOUS_SHA or transition['state']!='complete'
        or transition['previous_sha256']!=PREVIOUS_SHA
        or transition['next']['contract_sha256']!=sha256(new).hexdigest()):
        raise ValueError('Existing VIP authorization or consecutive transition changed')
    validate_revision(json.loads(old),json.loads(new))
    protected_tests(state,source,81)
    return check_frozen_sources(source,manifest['frozen'])
