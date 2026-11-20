"""Authenticate this run's explicit doubled aggregate grant; never reset usage."""
from hashlib import sha256
import json
from pathlib import Path

LIMITS=[250000000,24000000,160,2]
RECOVERY='lobby-double-v66'


def reusable_source(owned: tuple[str,...], actual: dict[str,str], frozen: dict[str,str]) -> bool:
    if not owned or any(p not in frozen for p in owned):return False
    if any(actual.get(p)!=frozen[p] for p in owned):raise ValueError('Frozen author source drifted')
    return True


def validate_grant(intent: dict, approval: dict, ledger: dict) -> dict:
    before=json.loads(bytes.fromhex(intent['saved']['budget.json']));after=intent['budget_after']
    if (approval!={'reply':'Double those ceilings','authority':'explicit_user_session','limits':LIMITS}
        or intent['state']!='complete' or before['limits']!=[125000000,12000000,80,2]
        or after['limits']!=LIMITS or ledger['limits']!=LIMITS
        or any(intent['authorization'].get(k)!=n for k,n in
               (('input_limit',250000000),('output_limit',24000000),('max_cycles',160)))
        or any(after['calls'].get(k)!=v for k,v in before['calls'].items())
        or any(after['cycles'].get(k)!=v for k,v in before['cycles'].items())
        or any(ledger['calls'].get(k)!=v for k,v in after['calls'].items())
        or any(ledger['cycles'].get(k)!=v for k,v in after['cycles'].items())):
        raise ValueError('Explicit doubling and unchanged complete accounting history required')
    return before


def frozen_inventory(previous: bytes, manifest: dict) -> dict[str,str]:
    frozen=json.loads(previous)['tdd']['frozen']
    if (sha256(previous).hexdigest()!=manifest['previous_services_sha256']
        or len(frozen)!=189 or manifest['frozen']!=frozen):
        raise ValueError('All 189 actual frozen inputs must survive recovery')
    return frozen


def activation(state: Path, ledger: dict, original: list[int]) -> list[int]:
    run=state/'.agent/runs/monopoly-game-lobby'
    intent=json.loads((run/'recoveries'/(RECOVERY+'.json')).read_bytes())
    approval=json.loads((state/'budget-amendments/double-v66-user-approval.json').read_bytes())
    before=validate_grant(intent,approval,ledger)
    from frozen_budget_continuation import activation_limits
    return activation_limits(state,before['limits'],before,original)


def protect(state: Path,source: Path,version: int,manifest: dict) -> tuple[str,...]:
    from frozen_budget_continuation import check_contract_continuity,check_frozen_sources
    if version!=67 or manifest['version']!=67 or manifest['recovery_id']!=RECOVERY:
        raise ValueError('Doubled continuation belongs to cycle 67 only')
    run=state/'.agent/runs/monopoly-game-lobby'
    ledger=json.loads((run/'budget.json').read_bytes())
    original=json.loads(Path(__file__).with_name('codex-backend.proposed.json').read_bytes())['preserve_aggregate_limits']
    activation(state,ledger,original)
    intent=json.loads((run/'recoveries'/(RECOVERY+'.json')).read_bytes())
    old=(source/'specs/monopoly-game-lobby/contract.v66.json').read_bytes()
    current=(source/'specs/monopoly-game-lobby/contract.v67.json').read_bytes()
    if intent['next']['contract_sha256']!=sha256(current).hexdigest():raise ValueError('Recovery contract changed')
    check_contract_continuity(json.loads(old),json.loads(current),sha256(old).hexdigest())
    frozen=frozen_inventory((run/'services-v66/state.json').read_bytes(),manifest)
    return check_frozen_sources(source,frozen)
