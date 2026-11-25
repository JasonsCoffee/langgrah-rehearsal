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


def appearance_first(units: list[dict]) -> list[dict]:
    appearance=next(unit for unit in units if unit['id']=='TEST-APPEAR')
    if appearance['depends_on']!=['TEST-HARNESS']:
        raise ValueError('Appearance review order must retain its harness dependency')
    harness=next(unit for unit in units if unit['id']=='TEST-HARNESS')
    return [harness,appearance,*[unit for unit in units if unit['id'] not in ('TEST-HARNESS','TEST-APPEAR')]]


def vip_retry_first(units: list[dict]) -> list[dict]:
    # The authored dependency files already exist and remain protected.
    return sorted(units,key=lambda unit: unit['id']!='TEST-VIP')


def protected_tests(state: Path, source: Path, version: int) -> tuple[str,...]:
    path=state/'frozen-continuations'/('v'+str(version)+'.json')
    if not path.exists():
        if path.parent.exists() and any(path.parent.glob('v*.json')):
            raise ValueError('Existing frozen tests require an explicit continuation for this cycle')
        return ()
    manifest=json.loads(path.read_bytes())
    if manifest.get('kind')=='approved_match_followup_v94':
        from approved_match_followup_v94 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_vip_followup_v92':
        from approved_vip_followup_v92 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='queue_review_context_v91':
        from queue_review_context_v91 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_match_reconciliation_v89':
        from approved_match_reconciliation_v89 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_appearance_followup_v88':
        from approved_appearance_followup_v88 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_vip_followup_v87':
        from approved_vip_followup_v87 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_cards_followup_v86':
        from approved_cards_followup_v86 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_vip_followup_v85':
        from approved_vip_followup_v85 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation_v83':
        from approved_test_reconciliation_v83 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation_v82':
        from approved_test_reconciliation_v82 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='vip_first_review_v80':
        from approved_test_reconciliation_v79 import protect_review_order
        return protect_review_order(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation_v79':
        from approved_test_reconciliation_v79 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='period_110m_scoped_recovery':
        from lobby_budget_period import EXTENSION_110_ID, period_usage
        run=state/'.agent/runs/monopoly-game-lobby'
        spec=source/'specs/monopoly-game-lobby'
        old=(spec/'contract.v92.json').read_bytes()
        new=(spec/'contract.v93.json').read_bytes()
        intent=json.loads((run/'recoveries'/(EXTENSION_110_ID+'.json')).read_bytes())
        if (version!=93 or manifest['version']!=93 or manifest['recovery_id']!=EXTENSION_110_ID
            or intent['candidate']!=manifest['prior_candidate']
            or intent['authorization']['previous_sha256']!=sha256(old).hexdigest()
            or intent['next']['contract_sha256']!=sha256(new).hexdigest()):
            raise ValueError('Exact native budget recovery provenance required')
        period_usage(state,json.loads((run/'budget.json').read_bytes()))
        old_contract=json.loads(old)
        check_contract_continuity(old_contract,json.loads(new),sha256(old).hexdigest())
        prior=protected_tests(state,source,92)
        inventory=json.loads((state/'frozen-continuations/v92.json').read_bytes())['frozen']
        if manifest['frozen']!={path:inventory[path] for path in prior}:
            raise ValueError('Budget recovery changed the frozen test scope')
        return check_frozen_sources(source,manifest['frozen'])
    if manifest.get('kind')=='period_90m_scoped_recovery':
        from lobby_budget_period import EXTENSION_90_ID, period_usage
        run=state/'.agent/runs/monopoly-game-lobby'
        spec=source/'specs/monopoly-game-lobby'
        old=(spec/'contract.v89.json').read_bytes()
        new=(spec/'contract.v90.json').read_bytes()
        intent=json.loads((run/'recoveries'/(EXTENSION_90_ID+'.json')).read_bytes())
        if (version!=90 or manifest['version']!=90 or manifest['recovery_id']!=EXTENSION_90_ID
            or intent['candidate']!=manifest['prior_candidate']
            or intent['authorization']['previous_sha256']!=sha256(old).hexdigest()
            or intent['next']['contract_sha256']!=sha256(new).hexdigest()):
            raise ValueError('Exact native budget recovery provenance required')
        period_usage(state,json.loads((run/'budget.json').read_bytes()))
        old_contract=json.loads(old)
        check_contract_continuity(old_contract,json.loads(new),sha256(old).hexdigest())
        prior=protected_tests(state,source,89)
        inventory=json.loads((state/'frozen-continuations/v89.json').read_bytes())['frozen']
        if manifest['frozen']!={path:inventory[path] for path in prior}:
            raise ValueError('Budget recovery changed the frozen test scope')
        return check_frozen_sources(source,manifest['frozen'])
    if manifest.get('kind')=='period_70m_scoped_recovery':
        from lobby_budget_period import EXTENSION_70_ID, period_usage
        run=state/'.agent/runs/monopoly-game-lobby'
        spec=source/'specs/monopoly-game-lobby'
        old=(spec/'contract.v83.json').read_bytes()
        new=(spec/'contract.v84.json').read_bytes()
        intent=json.loads((run/'recoveries'/(EXTENSION_70_ID+'.json')).read_bytes())
        if (version!=84 or manifest['version']!=84 or manifest['recovery_id']!=EXTENSION_70_ID
            or intent['candidate']!=manifest['prior_candidate']
            or intent['authorization']['previous_sha256']!=sha256(old).hexdigest()
            or intent['next']['contract_sha256']!=sha256(new).hexdigest()):
            raise ValueError('Exact native budget recovery provenance required')
        period_usage(state,json.loads((run/'budget.json').read_bytes()))
        old_contract=json.loads(old)
        check_contract_continuity(old_contract,json.loads(new),sha256(old).hexdigest())
        prior=protected_tests(state,source,83)
        inventory=json.loads((state/'frozen-continuations/v83.json').read_bytes())['frozen']
        if manifest['frozen']!={path:inventory[path] for path in prior}:
            raise ValueError('Budget recovery changed the frozen test scope')
        return check_frozen_sources(source,manifest['frozen'])
    if manifest.get('kind')=='period_50m_scoped_recovery':
        from lobby_budget_period import EXTENSION_50_ID, period_usage
        run=state/'.agent/runs/monopoly-game-lobby'
        spec=source/'specs/monopoly-game-lobby'
        old=(spec/'contract.v80.json').read_bytes()
        new=(spec/'contract.v81.json').read_bytes()
        intent=json.loads((run/'recoveries'/(EXTENSION_50_ID+'.json')).read_bytes())
        if (version!=81 or manifest['version']!=81 or manifest['recovery_id']!=EXTENSION_50_ID
            or intent['candidate']!=manifest['prior_candidate']
            or intent['authorization']['previous_sha256']!=sha256(old).hexdigest()
            or intent['next']['contract_sha256']!=sha256(new).hexdigest()):
            raise ValueError('Exact native budget recovery provenance required')
        period_usage(state,json.loads((run/'budget.json').read_bytes()))
        old_contract=json.loads(old)
        old_contract['units']=vip_retry_first(old_contract['units'])
        check_contract_continuity(old_contract,json.loads(new),sha256(old).hexdigest())
        prior=protected_tests(state,source,80)
        inventory=json.loads((state/'frozen-continuations/v80.json').read_bytes())['frozen']
        if manifest['frozen']!={path:inventory[path] for path in prior}:
            raise ValueError('Budget recovery changed the frozen test scope')
        return check_frozen_sources(source,manifest['frozen'])
    if manifest.get('kind')=='period_40m_scoped_recovery':
        from lobby_budget_period import EXTENSION_40_ID, period_usage
        run=state/'.agent/runs/monopoly-game-lobby'
        spec=source/'specs/monopoly-game-lobby'
        old=(spec/'contract.v77.json').read_bytes()
        new=(spec/'contract.v78.json').read_bytes()
        intent=json.loads((run/'recoveries'/(EXTENSION_40_ID+'.json')).read_bytes())
        if (version!=78 or manifest['version']!=78 or manifest['recovery_id']!=EXTENSION_40_ID
            or intent['candidate']!=manifest['prior_candidate']
            or intent['authorization']['previous_sha256']!=sha256(old).hexdigest()
            or intent['next']['contract_sha256']!=sha256(new).hexdigest()):
            raise ValueError('Exact native budget recovery provenance required')
        period_usage(state,json.loads((run/'budget.json').read_bytes()))
        old_contract=json.loads(old)
        old_contract['units']=appearance_first(old_contract['units'])
        check_contract_continuity(old_contract,json.loads(new),sha256(old).hexdigest())
        prior=protected_tests(state,source,77)
        inventory=json.loads((state/'frozen-continuations/v77.json').read_bytes())['frozen']
        if manifest['frozen']!={path:inventory[path] for path in prior}:
            raise ValueError('Budget recovery changed the frozen test scope')
        return check_frozen_sources(source,manifest['frozen'])
    if manifest.get('kind')=='period_30m_scoped_recovery':
        from lobby_budget_period import EXTENSION_ID, period_usage
        run=state/'.agent/runs/monopoly-game-lobby'
        spec=source/'specs/monopoly-game-lobby'
        old=(spec/'contract.v76.json').read_bytes()
        new=(spec/'contract.v77.json').read_bytes()
        intent=json.loads((run/'recoveries'/(EXTENSION_ID+'.json')).read_bytes())
        if (version!=77 or manifest['version']!=77 or manifest['recovery_id']!=EXTENSION_ID
            or intent['candidate']!=manifest['prior_candidate']
            or intent['authorization']['previous_sha256']!=sha256(old).hexdigest()
            or intent['next']['contract_sha256']!=sha256(new).hexdigest()):
            raise ValueError('Exact native budget recovery provenance required')
        period_usage(state,json.loads((run/'budget.json').read_bytes()))
        check_contract_continuity(json.loads(old),json.loads(new),sha256(old).hexdigest())
        prior=protected_tests(state,source,76)
        inventory=json.loads((state/'frozen-continuations/v76.json').read_bytes())['frozen']
        if manifest['frozen']!={path:inventory[path] for path in prior}:
            raise ValueError('Budget recovery changed the frozen test scope')
        return check_frozen_sources(source,manifest['frozen'])
    if manifest.get('kind')=='approved_test_reconciliation_v76':
        from approved_test_reconciliation_v76 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='reviewed_source_supplement':
        from reviewed_source_supplement import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation':
        from approved_test_reconciliation import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind') in ('approved_test_reconciliation_v71','carry_scoped_reconciliation_v71'):
        from approved_test_reconciliation_v71 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation_v75':
        from approved_test_reconciliation_v75 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation_v74':
        from approved_test_reconciliation_v74 import protect
        return protect(state,source,version,manifest)
    if manifest.get('kind')=='approved_test_reconciliation_v73':
        from approved_test_reconciliation_v73 import protect
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
