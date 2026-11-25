"""Continue the existing VIP helper approval after a fresh source rejection."""
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from approved_test_reconciliation import validate_method_change
from approved_test_reconciliation_v79 import REPLY, SCOPE as VIP_APPROVAL
from approved_test_reconciliation_v83 import author_paths as cards_paths
from frozen_budget_continuation import check_frozen_sources, protected_tests
from lobby_budget_period import period_usage
from operational_transport import retained_run_reservations
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

if TYPE_CHECKING:
    from unity_coder.core.contracts import Contract
    from unity_coder.core.local_executor import LocalExecutionServices

VERSION = 85
RUN_ID = 'monopoly-game-lobby'
CANDIDATE = '44e5611d53f53e02c9a262728d502fdce6e65e6d'
PREVIOUS_SHA = 'c6beba189a2c48d8439ee34c44f6190eb59742caa61649e9e7bac4ccf9f36522'
SCOPE = {'TEST-VIP': {'path': VIP_APPROVAL['TEST-VIP']['path'],
                      'methods': ['ContainsDistinctAmountField']}}
REVIEW = 'v84-step2-prepare-review-TEST-VIP'


def author_paths(unit: str) -> tuple[str, ...]:
    note = 'Tests/Runtime/Script/LobbyRehearsal/TEST-VIP.decimal-field-v85.md'
    return SCOPE[unit]['path'], note, note + '.meta'


def validate_patch(unit: str, patch: dict[str, bytes], source: Path) -> None:
    path = SCOPE[unit]['path']
    if path not in patch or set(patch) - set(author_paths(unit)):
        raise ValueError('VIP follow-up must contain only the scoped source and provenance')
    validate_method_change((source / path).read_bytes(), patch[path], tuple(SCOPE[unit]['methods']))


def revise(old: dict) -> dict:
    vip = next(unit for unit in old['units'] if unit['id'] == 'TEST-VIP')
    _, note, metadata = author_paths('TEST-VIP')
    guidance = (
        '\nCycle 85 reopens only ContainsDistinctAmountField under the prior approval. Reject '
        'VIP2：.3000 and equivalent decimal/grouping fragments with intervening horizontal spaces, '
        'including punctuation connected to the amount through currency markers. Treat numeric '
        'punctuation as part of the numeric token whenever it could introduce a signed, decimal, '
        'or grouped threshold. Recognize structural field separators explicitly. Check both token '
        'edges. Preserve valid VIP2：3000 and VIP2 累计充值：3000分, recognized recharge labels, and '
        'all prior sign, wrong-unit, and unrelated-field checks. Keep all other source bytes fixed. '
        'Record the verified cases in ' + note + ' and write ' + metadata +
        ' with fileFormatVersion: 2 newline guid: ' + sha256(note.encode()).hexdigest()[:32] + ' newline.'
    )
    revised = vip | {'owns': vip['owns'] + [note, metadata],
                     'instructions': vip['instructions'] + guidance}
    # Earlier units already have authored source. Only the VIP helper may be repaired.
    return old | {'contract_version': VERSION, 'previous_contract_sha256': PREVIOUS_SHA,
                  'units': [revised, *(unit for unit in old['units'] if unit['id'] != 'TEST-VIP')]}


def evidence(state: Path, module: Path, result_raw: bytes) -> tuple[dict[str, str], dict]:
    run = state / '.agent/runs' / RUN_ID
    result = json.loads(result_raw)
    if (result['outcome'], result['contract_version'], result['contract_sha256'],
        result['candidate_revision']) != ('rework', 84, PREVIOUS_SHA, CANDIDATE):
        raise ValueError('Exact cycle-84 VIP rework required')
    approval = json.loads((state / 'model-authorizations/test-reconciliation-v79.json').read_bytes())
    if approval != {'authority': 'explicit_user_session', 'reply': REPLY, 'version': 79, 'scope': VIP_APPROVAL}:
        raise ValueError('Prior VIP helper authorization changed')
    previous = state.parent / 'worktrees/architect-v84'
    old_inventory = json.loads((state / 'frozen-continuations/v84.json').read_bytes())['frozen']
    protected = protected_tests(state, previous, 84)
    services = (run / 'services-v84/state.json').read_bytes()
    tdd = json.loads(services)
    dossier = (run / 'dossier-v84.json').read_bytes()
    failed = json.loads(dossier)['failed_units']
    reply = (run / 'model-calls' / (sha256(REVIEW.encode()).hexdigest() + '.json')).read_bytes()
    decision = json.loads(json.loads(reply)['reply']['text'])
    if (tdd['candidate_revision'] != CANDIDATE or tdd['tdd']['frozen']
        or 'TEST-CARDS' not in tdd['tdd']['reviews'] or decision['valid'] is not False
        or 'VIP2：.3000' not in decision['explanation'] or [u['id'] for u in failed] != ['TEST-VIP']):
        raise ValueError('Cards approval and exact VIP rejection required')
    inventory = {path: old_inventory[path] for path in protected}
    for path in cards_paths('TEST-CARDS'):
        inventory[path] = sha256(git(module, 'show', CANDIDATE + ':' + path)).hexdigest()
    del inventory[SCOPE['TEST-VIP']['path']]
    return inventory, {'kind': 'approved_vip_followup_v85', 'version': VERSION,
                       'previous_result_sha256': sha256(result_raw).hexdigest(),
                       'dossier_sha256': sha256(dossier).hexdigest(),
                       'previous_services_sha256': sha256(services).hexdigest(),
                       'review_sha256': sha256(reply).hexdigest(), 'frozen': inventory}


def protect(state: Path, source: Path, version: int, manifest: dict) -> tuple[str, ...]:
    run = state / '.agent/runs' / RUN_ID
    result = (run / 'cycles/v84/result.json').read_bytes()
    inventory, expected = evidence(state, state.parent / 'module', result)
    spec = source / 'specs/monopoly-game-lobby'
    old = (spec / 'contract.v84.json').read_bytes()
    new = (spec / 'contract.v85.json').read_bytes()
    transition = json.loads((run / 'transitions/v85.json').read_bytes())
    if (version != VERSION or manifest != expected or sha256(old).hexdigest() != PREVIOUS_SHA
        or json.loads(new) != revise(json.loads(old)) or transition['state'] != 'complete'
        or transition['previous_sha256'] != PREVIOUS_SHA
        or transition['next']['contract_sha256'] != sha256(new).hexdigest()):
        raise ValueError('VIP follow-up scope or native transition changed')
    return check_frozen_sources(source, inventory)


def reconcile_incomplete_author(state: Path, contract: 'Contract', budget: BudgetLedger,
                                services: 'LocalExecutionServices') -> bool:
    """Keep the failed call fully charged and prove there is no partial patch."""
    run = state / '.agent/runs' / RUN_ID
    result = json.loads((run / 'result.json').read_bytes())
    start = json.loads((state / 'current-execution.json').read_bytes())
    stage = 'v85-step1-prepare'
    operation = stage + '-TEST-VIP-TEST-VIP'
    source = services.integration.path
    tx = services.effects.read('transaction')
    candidate = start['candidate']
    if (contract.contract_version != VERSION or start['version'] != VERSION
        or result['contract_sha256'] != contract.sha256 or start['contract_sha256'] != contract.sha256
        or result['outcome'] != 'operational' or result['candidate_revision'] != candidate
        or result['reason'] != 'Model transport requires reconciliation'
        or tx['operation'] != stage or tx['stage'] != 'prepare' or not tx['complete']
        or git(source, 'rev-parse', 'HEAD').decode().strip() != candidate or git(source, 'status', '--porcelain')
        or services.effects.read('worker-' + operation) !=
           {'identity': {'stage': 'test_authoring', 'unit': 'TEST-VIP', 'base': candidate}}
        or services.effects.read('apply-' + operation) is not None or services.tdd.frozen
        or (state / 'anchored-author' / (operation + '.complete.json')).exists()):
        raise ValueError('Exact unadmitted cycle-85 authoring stop required')
    ledger = budget._read()
    period_usage(state, ledger)
    retained_run_reservations(state, ledger)
    raw = (run / 'model-calls' / (sha256(operation.encode()).hexdigest() + '.json')).read_bytes()
    record = json.loads(raw)
    identity = record['identity']
    charge = ledger['calls'][operation]
    if (identity['call_id'] != operation or identity['unit_id'] != 'TEST-VIP'
        or identity['role'] != 'coder' or identity['provider'] != 'deepseek'
        or record.get('failure') != {'input_tokens': 138676, 'output_tokens': 1976}
        or 'reply' in record or charge.get('actual') != [138676, 1976]):
        raise ValueError('Exact settled incomplete author response required')
    atomic_write(state, 'host-reconciliations/v85-incomplete-vip.json', json.dumps({
        'candidate': candidate, 'contract_sha256': contract.sha256, 'operation': operation,
        'receipt_sha256': sha256(raw).hexdigest(), 'actual': charge['actual'],
        'patch_admitted': False, 'human_accepted': False}, indent=2).encode())
    return True


def main() -> None:
    framework = Path.cwd().resolve()
    root = Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state, module = root / 'trusted-state', root / 'module'
    run = state / '.agent/runs' / RUN_ID
    raw = (run / 'result.json').read_bytes()
    inventory, manifest = evidence(state, module, raw)
    policy = json.loads((state / 'budget-policy.json').read_bytes())
    if policy.pop('run_id') != RUN_ID:
        raise ValueError('Budget belongs to another run')
    budget = BudgetLedger(state, RUN_ID, **policy)
    period_usage(state, budget._read())
    retained_run_reservations(state, budget._read())
    source = root / 'worktrees/architect-v85'
    context = discover_context(framework, json.loads((framework / '.agent/lobby-apply.json').read_bytes()),
                               sources=json.loads((framework / '.agent/lobby-sources.json').read_bytes()))
    lease = RunLease(state, RUN_ID, 'approved-vip-followup-v85-' + str(os.getpid()))
    lease.acquire(owner_alive=lambda _: True)
    try:
        if source.exists():
            raise ValueError('Preserve existing VIP follow-up preparation')
        git(module, 'worktree', 'add', '-b', 'codex/lobby-architect-v85', str(source), CANDIDATE)
        check_frozen_sources(source, inventory)
        spec = source / 'specs/monopoly-game-lobby'
        old = (spec / 'contract.v84.json').read_bytes()
        if sha256(old).hexdigest() != PREVIOUS_SHA:
            raise ValueError('Previous contract changed')
        relative = 'specs/monopoly-game-lobby/contract.v85.json'
        (source / relative).write_text(json.dumps(revise(json.loads(old)), ensure_ascii=False, indent=2) + '\n',
                                      encoding='utf-8', newline='\n')
        rules = UnityAdapter()
        contracts = []
        for version in range(1, VERSION + 1):
            contracts.append(load_contract((spec / f'contract.v{version}.json').read_bytes(), source, rules,
                                           previous=contracts[-1] if contracts else None, max_cycles=120))
        git(source, 'add', '--', relative)
        git(source, '-c', 'user.name=Lobby Rehearsal', '-c', 'user.email=rehearsal@example.invalid',
            'commit', '-m', 'Continue previously approved VIP helper correction')

        def reconciled() -> bool:
            transaction = json.loads((run / 'services-v84/effects/transaction.json').read_bytes())
            check_frozen_sources(source, inventory)
            return transaction['complete'] is True and not git(source, 'status', '--porcelain')

        atomic_write(state, 'frozen-continuations/v85.json', json.dumps(manifest, indent=2).encode())
        transition_cycle(framework, state, RUN_ID, contracts[-2], contracts[-1], context, budget, lease,
                         workers_reconciled=reconciled)
        restoration = json.loads((state / 'baseline-restorations/v84.json').read_bytes())
        restoration['tests'] = inventory
        atomic_write(state, 'baseline-restorations/v85.json', json.dumps(restoration, indent=2).encode())
        active = {'version': VERSION, 'candidate': git(source, 'rev-parse', 'HEAD').decode().strip(),
                  'contract_source': 'architect-v85', 'contract_sha256': contracts[-1].sha256}
        atomic_write(state, 'current-execution.json', json.dumps(active, indent=2).encode())
        print(json.dumps(active | {'token_period_usage': period_usage(state, budget._read())[0],
                                   'protected_source_files': len(inventory)}), flush=True)
    finally:
        lease.release()


if __name__ == '__main__':
    main()
