"""Keep an existing frozen test set protected across a native budget amendment."""
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.ownership import confined_path


def check_frozen_sources(source: Path, hashes: dict[str,str]) -> tuple[str,...]:
    if not hashes:raise ValueError('A frozen continuation must retain its complete test map')
    for path,digest in hashes.items():
        if sha256(confined_path(source,path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Frozen continuation source drift: '+path)
    return tuple(hashes)


def check_contract_continuity(previous: dict, current: dict, digest: str) -> None:
    expected=previous|{'contract_version':previous['contract_version']+1,'previous_contract_sha256':digest}
    if current!=expected:raise ValueError('Budget continuation cannot revise ownership, instructions or criteria')


def protected_tests(state: Path, source: Path, version: int) -> tuple[str,...]:
    path=state/'frozen-continuations'/('v'+str(version)+'.json')
    if not path.exists():
        if path.parent.exists() and any(path.parent.glob('v*.json')):
            raise ValueError('Existing frozen tests require an explicit continuation for this cycle')
        return ()
    manifest=json.loads(path.read_bytes())
    if manifest.get('kind')=='reviewed_source_supplement':
        from reviewed_source_supplement import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation':
        from approved_test_reconciliation import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='doubled_budget':
        from doubled_budget_continuation import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='supplemental_frozen_coverage':
        from supplemental_frozen_coverage import validate_manifest
        return check_frozen_sources(source,validate_manifest(state,source,version,manifest))
    if manifest.get('kind')=='implementation_rework':
        from frozen_implementation_rework import validate_manifest
        return check_frozen_sources(source,validate_manifest(state,source,version,manifest))
    run=state/'.agent/runs/monopoly-game-lobby'
    intent=json.loads((run/'recoveries'/(manifest['recovery_id']+'.json')).read_bytes())
    old_version=version-1
    old_state=(run/('services-v'+str(old_version))/'state.json').read_bytes()
    old_contract=(source/'specs/monopoly-game-lobby'/('contract.v'+str(old_version)+'.json')).read_bytes()
    current_contract=(source/'specs/monopoly-game-lobby'/('contract.v'+str(version)+'.json')).read_bytes()
    frozen=json.loads(old_state)['tdd']['frozen']
    if (manifest['version']!=version or manifest['previous_services_sha256']!=sha256(old_state).hexdigest()
        or manifest['frozen']!=frozen or not frozen or len(frozen)!=185
        or intent['state']!='complete' or intent['authorization']['input_limit']!=125000000
        or intent['authorization']['output_limit']!=12000000 or intent['authorization']['max_cycles']!=80
        or intent['next']['contract_sha256']!=sha256(current_contract).hexdigest()):
        raise ValueError('Frozen continuation lacks matching completed native recovery')
    check_contract_continuity(json.loads(old_contract),json.loads(current_contract),sha256(old_contract).hexdigest())
    return check_frozen_sources(source,frozen)


def activation_limits(state: Path, limits: list[int], ledger: dict, original: list[int]) -> list[int]:
    """A historical backend grant stays immutable; native token authority is separate."""
    if limits==original:return original
    if limits==[250000000,24000000,160,2]:
        from doubled_budget_continuation import activation
        return activation(state,ledger,original)
    if limits!=[125000000,12000000,80,2]:raise ValueError('Unrecognized Codex aggregate amendment')
    run=state/'.agent/runs/monopoly-game-lobby'
    intent=json.loads((run/'recoveries/lobby-extend-125m.json').read_bytes())
    approval=json.loads((state/'budget-amendments/input-125m-user-approval.json').read_bytes())
    before=json.loads(bytes.fromhex(intent['saved']['budget.json']))
    after=intent['budget_after']
    if (intent['state']!='complete' or before['limits']!=original or after['limits']!=limits
        or approval['reply']!='Approve 125M input; keep 12M output / 80 cycles'
        or intent['authorization']['input_limit']!=125000000
        or intent['authorization']['output_limit']!=12000000 or intent['authorization']['max_cycles']!=80
        or any(ledger['calls'].get(k)!=v for k,v in after['calls'].items())
        or any(ledger['cycles'].get(k)!=v for k,v in after['cycles'].items())):
        raise ValueError('Codex token amendment lost native authorization or retained charges')
    return original
