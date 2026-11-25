"""Continue the existing Match fee approval after a fresh source rejection."""
from hashlib import sha256
import json
import os
from pathlib import Path

from approved_test_reconciliation import validate_method_change
from approved_match_reconciliation_v89 import APPROVAL, APPROVAL_REF, SCOPE as MATCH_APPROVAL
from approved_vip_followup_v92 import author_paths as vip_paths
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

VERSION = 94
RUN_ID = 'monopoly-game-lobby'
CANDIDATE = 'cac13b381b03a59637312a854675986289224908'
PREVIOUS_SHA = '39b3a1d21e6f290b715ecf5c8586cc0afd8d9ff151086fe771c4091924ba4af4'
SCOPE = {'TEST-MATCH': {'path': MATCH_APPROVAL['TEST-MATCH']['path'],
                        'methods': ['AssertDisplayedFee']}}
REVIEW = 'v93-step2-prepare-review-TEST-MATCH'


def author_paths(unit: str) -> tuple[str, ...]:
    note = 'Tests/Runtime/Script/LobbyRehearsal/TEST-MATCH.projected-glyphs-v94.md'
    return SCOPE[unit]['path'], note, note + '.meta'


def validate_patch(unit: str, patch: dict[str, bytes], source: Path) -> None:
    path = SCOPE[unit]['path']
    if path not in patch or set(patch) - set(author_paths(unit)):
        raise ValueError('Match fee follow-up must contain only the scoped source and provenance')
    validate_method_change((source / path).read_bytes(), patch[path], tuple(SCOPE[unit]['methods']))


def revise(old: dict) -> dict:
    match = next(unit for unit in old['units'] if unit['id'] == 'TEST-MATCH')
    _, note, metadata = author_paths('TEST-MATCH')
    guidance = (
        '\nCycle 94 reopens only AssertDisplayedFee under the original Match approval. For each '
        'matched fee digit, require a finite positive measurable area from the actual glyph '
        'corners after transform and projection to screen space. A degenerate quad, including '
        'zero scale along one local axis or total zero scale, must fail even if local TMP bounds, '
        'opacity and containment are valid. Use the actual camera appropriate to the canvas. '
        'Retain the exact amount, label binding, material-specific vertex opacity, cull and '
        'glyph clipping checks. Preserve Story_L9_03 and every other source byte. '
        'Record the checks in ' + note + ' and write ' + metadata +
        ' with fileFormatVersion: 2 newline guid: ' + sha256(note.encode()).hexdigest()[:32] + ' newline.'
    )
    revised = match | {'owns': match['owns'] + [note, metadata],
                       'instructions': match['instructions'] + guidance}
    return old | {'contract_version': VERSION, 'previous_contract_sha256': PREVIOUS_SHA,
                  'units': [revised, *(unit for unit in old['units'] if unit['id'] != 'TEST-MATCH')]}


def evidence(state: Path, module: Path, result_raw: bytes) -> tuple[dict[str, str], dict]:
    run = state / '.agent/runs' / RUN_ID
    result = json.loads(result_raw)
    if (result['outcome'], result['contract_version'], result['contract_sha256'],
        result['candidate_revision']) != ('rework', 93, PREVIOUS_SHA, CANDIDATE):
        raise ValueError('Exact cycle-93 Match rework required')
    approval = json.loads((state / APPROVAL_REF).read_bytes())
    if approval != APPROVAL:
        raise ValueError('Prior Match helper authorization changed')
    previous = state.parent / 'worktrees/architect-v93'
    old_inventory = json.loads((state / 'frozen-continuations/v93.json').read_bytes())['frozen']
    protected = protected_tests(state, previous, 93)
    services = (run / 'services-v93/state.json').read_bytes()
    tdd = json.loads(services)
    dossier = (run / 'dossier-v93.json').read_bytes()
    failed = json.loads(dossier)['failed_units']
    reply = (run / 'model-calls' / (sha256(REVIEW.encode()).hexdigest() + '.json')).read_bytes()
    decision = json.loads(json.loads(reply)['reply']['text'])
    if (tdd['candidate_revision'] != CANDIDATE or tdd['tdd']['frozen']
        or 'TEST-VIP' not in tdd['tdd']['reviews'] or decision['valid'] is not False
        or 'screen-space glyph area' not in decision['explanation'] or [u['id'] for u in failed] != ['TEST-MATCH']):
        raise ValueError('VIP approval and exact Match rejection required')
    inventory = {path: old_inventory[path] for path in protected}
    for path in vip_paths('TEST-VIP'):
        inventory[path] = sha256(git(module, 'show', CANDIDATE + ':' + path)).hexdigest()
    del inventory[SCOPE['TEST-MATCH']['path']]
    return inventory, {'kind': 'approved_match_followup_v94', 'version': VERSION,
                       'previous_result_sha256': sha256(result_raw).hexdigest(),
                       'dossier_sha256': sha256(dossier).hexdigest(),
                       'previous_services_sha256': sha256(services).hexdigest(),
                       'review_sha256': sha256(reply).hexdigest(), 'frozen': inventory}


def protect(state: Path, source: Path, version: int, manifest: dict) -> tuple[str, ...]:
    run = state / '.agent/runs' / RUN_ID
    result = (run / 'cycles/v93/result.json').read_bytes()
    inventory, expected = evidence(state, state.parent / 'module', result)
    spec = source / 'specs/monopoly-game-lobby'
    old = (spec / 'contract.v93.json').read_bytes()
    new = (spec / 'contract.v94.json').read_bytes()
    transition = json.loads((run / 'transitions/v94.json').read_bytes())
    if (version != VERSION or manifest != expected or sha256(old).hexdigest() != PREVIOUS_SHA
        or json.loads(new) != revise(json.loads(old)) or transition['state'] != 'complete'
        or transition['previous_sha256'] != PREVIOUS_SHA
        or transition['next']['contract_sha256'] != sha256(new).hexdigest()):
        raise ValueError('Match follow-up scope or native transition changed')
    return check_frozen_sources(source, inventory)


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
    source = root / 'worktrees/architect-v94'
    context = discover_context(framework, json.loads((framework / '.agent/lobby-apply.json').read_bytes()),
                               sources=json.loads((framework / '.agent/lobby-sources.json').read_bytes()))
    lease = RunLease(state, RUN_ID, 'approved-match-followup-v94-' + str(os.getpid()))
    lease.acquire(owner_alive=lambda _: True)
    try:
        if source.exists():
            raise ValueError('Preserve existing Match follow-up preparation')
        git(module, 'worktree', 'add', '-b', 'codex/lobby-architect-v94', str(source), CANDIDATE)
        check_frozen_sources(source, inventory)
        spec = source / 'specs/monopoly-game-lobby'
        old = (spec / 'contract.v93.json').read_bytes()
        if sha256(old).hexdigest() != PREVIOUS_SHA:
            raise ValueError('Previous contract changed')
        relative = 'specs/monopoly-game-lobby/contract.v94.json'
        (source / relative).write_text(json.dumps(revise(json.loads(old)), ensure_ascii=False, indent=2) + '\n',
                                      encoding='utf-8', newline='\n')
        rules = UnityAdapter()
        contracts = []
        for version in range(1, VERSION + 1):
            contracts.append(load_contract((spec / f'contract.v{version}.json').read_bytes(), source, rules,
                                           previous=contracts[-1] if contracts else None, max_cycles=120))
        git(source, 'add', '--', relative)
        git(source, '-c', 'user.name=Lobby Rehearsal', '-c', 'user.email=rehearsal@example.invalid',
            'commit', '-m', 'Continue previously approved Match projected glyph geometry correction')

        def reconciled() -> bool:
            transaction = json.loads((run / 'services-v93/effects/transaction.json').read_bytes())
            check_frozen_sources(source, inventory)
            return transaction['complete'] is True and not git(source, 'status', '--porcelain')

        atomic_write(state, 'frozen-continuations/v94.json', json.dumps(manifest, indent=2).encode())
        transition_cycle(framework, state, RUN_ID, contracts[-2], contracts[-1], context, budget, lease,
                         workers_reconciled=reconciled)
        restoration = json.loads((state / 'baseline-restorations/v93.json').read_bytes())
        restoration['tests'] = inventory
        atomic_write(state, 'baseline-restorations/v94.json', json.dumps(restoration, indent=2).encode())
        active = {'version': VERSION, 'candidate': git(source, 'rev-parse', 'HEAD').decode().strip(),
                  'contract_source': 'architect-v94', 'contract_sha256': contracts[-1].sha256}
        atomic_write(state, 'current-execution.json', json.dumps(active, indent=2).encode())
        print(json.dumps(active | {'token_period_usage': period_usage(state, budget._read())[0],
                                   'protected_source_files': len(inventory)}), flush=True)
    finally:
        lease.release()


if __name__ == '__main__':
    main()
