"""Bind the Queue reviewer to the existing Architect seat rule and file inventory."""
from collections.abc import Callable, Mapping
from hashlib import sha256
import json
import os
from pathlib import Path

from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import Unit, load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.local_executor import LocalExecutionServices
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

from approved_match_reconciliation_v89 import author_paths as match_paths
from frozen_budget_continuation import check_frozen_sources, protected_tests
from lobby_budget_period import period_usage
from operational_transport import retained_run_reservations

RUN = 'monopoly-game-lobby'
SPEC = 'specs/monopoly-game-lobby/'
RULE = SPEC + 'seat-oracle.v34.md'
RULE_SHA = 'b9868bbf9b7105beac35f9cfb6dfa0ec9f7e7c6b2bd1fedfa847ee64952563f6'
PROFILE = SPEC + 'coding-profile.v91.json'
PREVIOUS = '27d812faab959e8ea56e7b7a89cbeacd9c43a7ed39243a997fdbca00e61408b7'
CANDIDATE = '8e417721876f2a278d63dc33210874e5128a29c7'
REVIEW = 'v90-step2-prepare-review-TEST-QUEUE'
NOTE_ROOT = 'Tests/Runtime/Script/LobbyRehearsal/LobbyMatchQueueTests.'
MAP = NOTE_ROOT + 'focused-v21.md'
NOTE = NOTE_ROOT + 'repair-v34.md'


def queue_review_inventory(unit: Unit, files: Mapping[str, str],
                           source_text: Callable[[str, str], str]) -> dict:
    rule = source_text(RULE, files[RULE])
    if sha256(rule.encode()).hexdigest() != RULE_SHA:
        raise ValueError('Queue requires the existing exact Architect seat allocation rule')
    inventory = {}
    for path in (MAP, NOTE, NOTE + '.meta'):
        if path not in unit.owns:
            raise ValueError('Queue evidence path is outside its declared ownership')
        content = source_text(path, files[path])
        inventory[path] = {'sha256': sha256(content.encode()).hexdigest(), 'present': True}
    inventory[NOTE + '.meta']['matches_required_guid'] = (
        files[NOTE + '.meta'].splitlines()
        == ['fileFormatVersion: 2', 'guid: fd36667ec0e6571caaff80d049f9ce56']
    )
    return inventory


def revised_profile(raw: bytes) -> bytes:
    profile = json.loads(raw)
    if any(rule['path'] == RULE for rule in profile['rules']):
        raise ValueError('Queue rule already in the previous profile')
    profile['rules'].append({'path': RULE, 'sha256': RULE_SHA})
    return (json.dumps(profile, ensure_ascii=False, indent=2) + '\n').encode()


def revision(previous: dict, profile: bytes) -> dict:
    return previous | {
        'contract_version': 91, 'previous_contract_sha256': PREVIOUS,
        'coding_profile_ref': {'path': PROFILE, 'sha256': sha256(profile).hexdigest()},
        'units': sorted(previous['units'], key=lambda unit: unit['id'] != 'TEST-QUEUE'),
    }


def evidence(state: Path, raw: bytes) -> dict:
    run = state / '.agent/runs' / RUN
    result = json.loads(raw)
    if (result['outcome'], result['contract_version'], result['contract_sha256'],
        result['candidate_revision']) != ('rework', 90, PREVIOUS, CANDIDATE):
        raise ValueError('Expected the exact Queue source review omission')
    dossier = (run / 'dossier-v90.json').read_bytes()
    previous = (run / 'services-v90/state.json').read_bytes()
    reviews = json.loads(previous)['tdd']
    key = sha256(REVIEW.encode()).hexdigest()
    reply = (run / 'model-calls' / (key + '.json')).read_bytes()
    verdict = json.loads(json.loads(reply)['reply']['text'])
    failed = json.loads(dossier)['failed_units']
    if (reviews['frozen'] or 'TEST-MATCH' not in reviews['reviews'] or verdict['valid'] is not False
        or 'seat-oracle.v34.md is absent' not in verdict['explanation']
        or [unit['id'] for unit in failed] != ['TEST-QUEUE']):
        raise ValueError('Expected Match approval and Queue evidence rejection')
    source = state.parent / 'worktrees/architect-v90'
    prior = json.loads((state / 'frozen-continuations/v90.json').read_bytes())['frozen']
    frozen = {path: prior[path] for path in protected_tests(state, source, 90)}
    for path in match_paths('TEST-MATCH'):
        frozen[path] = sha256(git(state.parent / 'module', 'show', CANDIDATE + ':' + path)).hexdigest()
    return {'kind': 'queue_review_context_v91', 'version': 91, 'frozen': frozen,
            'previous_result_sha256': sha256(raw).hexdigest(), 'review_sha256': sha256(reply).hexdigest(),
            'previous_state_sha256': sha256(previous).hexdigest(), 'dossier_sha256': sha256(dossier).hexdigest()}


def protect(state: Path, source: Path, version: int, manifest: dict) -> tuple[str, ...]:
    run = state / '.agent/runs' / RUN
    old = (source / (SPEC + 'contract.v90.json')).read_bytes()
    new = (source / (SPEC + 'contract.v91.json')).read_bytes()
    previous = json.loads(old)
    profile = revised_profile((source / previous['coding_profile_ref']['path']).read_bytes())
    transition = json.loads((run / 'transitions/v91.json').read_bytes())
    if (version != 91 or sha256(old).hexdigest() != PREVIOUS
        or evidence(state, (run / 'cycles/v90/result.json').read_bytes()) != manifest
        or (source / PROFILE).read_bytes() != profile or json.loads(new) != revision(previous, profile)
        or sha256((source / RULE).read_bytes()).hexdigest() != RULE_SHA
        or transition['state'] != 'complete' or transition['previous_sha256'] != PREVIOUS
        or transition['next']['contract_sha256'] != sha256(new).hexdigest()):
        raise ValueError('Queue review context provenance changed')
    return check_frozen_sources(source, manifest['frozen'])


def reconcile_judge_deadline(state: Path, budget: BudgetLedger, services: LocalExecutionServices) -> bool:
    from codex_context_recovery import register_retained_call

    run = state / '.agent/runs' / RUN
    candidate = '4b76091f709c6ca94790f7d0e447272f6e6bb2df'
    contract = 'ac8b930009e9ea8e95691c2be3ff9bc705664559f5005cee59544988425f734f'
    operation = 'v91-step1-prepare'
    call = operation + '-review-TEST-MATCH'
    key = sha256(call.encode()).hexdigest()
    digest = '745fc4e59bd7fb24c9baca10e53a072877d9f727b01f8f31be2af53cdd16e13b'
    path = services.integration.path
    result = json.loads((run / 'result.json').read_bytes())
    raw = (run / 'model-calls' / (key + '.json')).read_bytes()
    tx = services.effects.read('transaction')
    ledger = budget._read()
    charge = ledger['calls'][call]
    if (result['outcome'], result['reason'], result['candidate_revision'],
        result['contract_version'], result['contract_sha256']) != (
        'operational', 'Model transport requires reconciliation', candidate, 91, contract
    ) or (tx['operation'], tx['stage'], tx['complete']) != (operation, 'prepare', True) or (
        sha256(raw).hexdigest() != digest
        or json.loads(raw)['failure'] != {'transport': 'codex_stdio', 'failure_kind': 'deadline'}
        or charge != {'reserved': [5870268, 32768], 'unit': 'TEST-MATCH', 'version': 91}
        or services.effects.read('review-' + operation + '-TEST-MATCH') != {'identity': {'unit': 'TEST-MATCH'}}
        or services.tdd.frozen or 'TEST-QUEUE' not in services.tdd._reviews
        or git(path, 'rev-parse', 'HEAD').decode().strip() != candidate or git(path, 'status', '--porcelain')
    ):
        raise ValueError('Expected the exact Queue-approved Match review deadline')
    protected_tests(state, path, 91)
    historical = ledger | {'calls': {k: v for k, v in ledger['calls'].items() if k != call}}
    retained_run_reservations(state, historical)
    register_retained_call(state, call, charge, digest)
    retained_run_reservations(state, budget._read())
    atomic_write(state, 'host-reconciliations/v91-match-judge-deadline.json', json.dumps({
        'candidate': candidate, 'contract_sha256': contract, 'original_call': call, 'reservation': charge,
        'receipt_sha256': digest, 'original_call_replayed': False,
    }, sort_keys=True).encode())
    return True


def main() -> None:
    framework = Path.cwd().resolve()
    root = Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state = root / 'trusted-state'
    run = state / '.agent/runs' / RUN
    manifest = evidence(state, (run / 'result.json').read_bytes())
    policy = json.loads((state / 'budget-policy.json').read_bytes())
    if policy.pop('run_id') != RUN:
        raise ValueError('Budget belongs to another run')
    budget = BudgetLedger(state, RUN, **policy)
    period_usage(state, budget._read())
    retained_run_reservations(state, budget._read())
    source = root / 'worktrees/architect-v91'
    context = discover_context(framework, json.loads((framework / '.agent/lobby-apply.json').read_bytes()),
                               sources=json.loads((framework / '.agent/lobby-sources.json').read_bytes()))
    lease = RunLease(state, RUN, 'queue-review-context-v91-' + str(os.getpid()))
    lease.acquire(owner_alive=lambda _: True)
    try:
        if source.exists():
            raise ValueError('Preserve existing Queue review context preparation')
        git(root / 'module', 'worktree', 'add', '-b', 'codex/lobby-architect-v91', str(source), CANDIDATE)
        check_frozen_sources(source, manifest['frozen'])
        old = (source / (SPEC + 'contract.v90.json')).read_bytes()
        if sha256(old).hexdigest() != PREVIOUS or sha256((source / RULE).read_bytes()).hexdigest() != RULE_SHA:
            raise ValueError('Previous contract or Architect rule changed')
        previous = json.loads(old)
        profile = revised_profile((source / previous['coding_profile_ref']['path']).read_bytes())
        (source / PROFILE).write_bytes(profile)
        relative = SPEC + 'contract.v91.json'
        (source / relative).write_text(json.dumps(revision(previous, profile), ensure_ascii=False, indent=2) + '\n',
                                       encoding='utf-8', newline='\n')
        contracts = []
        rules = UnityAdapter()
        for version in range(1, 92):
            raw = (source / (SPEC + f'contract.v{version}.json')).read_bytes()
            contracts.append(load_contract(raw, source, rules, previous=contracts[-1] if contracts else None,
                                           max_cycles=120))
        git(source, 'add', '--', relative, PROFILE)
        git(source, '-c', 'user.name=Lobby Rehearsal', '-c', 'user.email=rehearsal@example.invalid',
            'commit', '-m', 'Bind existing seat allocation rule to Queue review')

        def reconciled() -> bool:
            tx = json.loads((run / 'services-v90/effects/transaction.json').read_bytes())
            check_frozen_sources(source, manifest['frozen'])
            return tx['complete'] is True and not git(source, 'status', '--porcelain')

        atomic_write(state, 'frozen-continuations/v91.json', json.dumps(manifest, indent=2).encode())
        transition_cycle(framework, state, RUN, contracts[-2], contracts[-1], context, budget, lease,
                         workers_reconciled=reconciled)
        restoration = json.loads((state / 'baseline-restorations/v90.json').read_bytes())
        restoration['tests'] = manifest['frozen']
        atomic_write(state, 'baseline-restorations/v91.json', json.dumps(restoration, indent=2).encode())
        active = {'version': 91, 'candidate': git(source, 'rev-parse', 'HEAD').decode().strip(),
                  'contract_source': 'architect-v91', 'contract_sha256': contracts[-1].sha256}
        atomic_write(state, 'current-execution.json', json.dumps(active, indent=2).encode())
        print(json.dumps(active | {'protected_source_files': len(manifest['frozen'])}), flush=True)
    finally:
        lease.release()


if __name__ == '__main__':
    main()
