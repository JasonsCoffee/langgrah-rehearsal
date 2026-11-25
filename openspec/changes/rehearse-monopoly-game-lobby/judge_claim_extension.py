"""Authorized same-run extension of the cumulative Codex Judge call limit."""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path

from unity_coder.core.codex_backend import CodexPolicy
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

RUN = 'monopoly-game-lobby'
REF = 'model-authorizations/judge-claims-250.json'
REPLY = 'Raise the Judge limit to 250'
CANDIDATE = '7106fb20a73fd5d53eab8b2b1d735f12d7c5f990'
CONTRACT = 'f132e672d13fb038ae7a13aef9bb2dff9428b8633df8157af298c147615a4b4e'
BLOCKED = 'v86-step1-prepare-review-TEST-VIP'


def run_path(state: Path) -> Path:
    return state / '.agent/runs' / RUN


def claim_archive(state: Path) -> dict[str, dict[str, str]]:
    records = {}
    for path in (run_path(state) / 'model-calls').glob('*.json'):
        raw = path.read_bytes()
        identity = json.loads(raw)['identity']
        if identity['role'] != 'judge' or identity.get('worker_backend') != 'codex_app_server':
            continue
        key = sha256(identity['call_id'].encode()).hexdigest()
        policy = identity['backend_policy_sha256']
        claim = state / 'codex-claims' / policy / (key + '.json')
        if claim.exists():
            claims = claim.read_bytes()
            if path.stem != key or json.loads(claims) != {
                'operation_id': identity['call_id'], 'policy_sha256': policy,
                'prompt_sha256': identity['prompt_sha256'],
            }:
                raise ValueError('Judge claim identity drift')
            records[identity['call_id']] = {'receipt': sha256(raw).hexdigest(),
                                           'claim': sha256(claims).hexdigest()}
    return records


def amended_policy(state: Path, base: CodexPolicy, ledger: dict) -> CodexPolicy:
    path = state / REF
    if not path.exists():
        return base
    grant = json.loads(path.read_bytes())
    policy = replace(base, max_calls=250, authorization_ref=REF)
    saved = grant['history']
    claims = claim_archive(state)
    if (grant['authority'], grant['reply'], grant['run'], grant['base_policy_sha256'],
        grant['policy_sha256'], base.max_calls, len(saved['claims'])) != (
        'explicit_user_session', REPLY, RUN, base.sha256, policy.sha256, 200, 200
    ) or ledger['limits'][0] < saved['limits'][0] or ledger['limits'][1:] != saved['limits'][1:] or any(
        ledger['calls'].get(k) != v for k, v in saved['calls'].items()
    ) or any(ledger['cycles'].get(k) != v for k, v in saved['cycles'].items()) or any(
        claims.get(k) != v for k, v in saved['claims'].items()
    ):
        raise ValueError('Judge limit extension requires matching approval and exact retained history')
    return policy


def verify_stop(state: Path, source: Path) -> bytes:
    run = run_path(state)
    raw = (run / 'result.json').read_bytes()
    result = json.loads(raw)
    service = run / 'services-v86'
    tx = json.loads((service / 'effects/transaction.json').read_bytes())
    tdd = json.loads((service / 'state.json').read_bytes())['tdd']
    key = sha256(BLOCKED.encode()).hexdigest()
    if (result['outcome'], result['reason'], result['candidate_revision'],
        result['contract_version'], result['contract_sha256']) != (
        'operational', 'Model transport requires reconciliation', CANDIDATE, 86, CONTRACT
    ) or (tx['operation'], tx['stage'], tx['complete']) != ('v86-step1-prepare', 'prepare', True) or (
        git(source, 'rev-parse', 'HEAD').decode().strip() != CANDIDATE
        or git(source, 'status', '--porcelain') or tdd['frozen']
        or set(tdd['reviews']) != {'TEST-CARDS'}
        or json.loads((service / 'effects/review-v86-step1-prepare-TEST-VIP.json').read_bytes())
        != {'identity': {'unit': 'TEST-VIP'}}
        or (run / 'model-calls' / (key + '.json')).exists()
        or (state / 'context-verdicts' / (key + '.json')).exists()
        or (state / 'review-reuse' / (key + '.json')).exists()
        or any((state / 'codex-claims').glob('*/' + key + '.json'))
    ):
        raise ValueError('Expected settled Cards approval and pre-dispatch VIP stop')
    return raw


def reconcile(state: Path, source: Path, ledger: dict, policy: CodexPolicy) -> bool:
    from mixed_backend_policy import judge_policy
    from operational_transport import retained_run_reservations

    raw = verify_stop(state, source)
    grant = json.loads((state / REF).read_bytes())
    if (policy != amended_policy(state, judge_policy(), ledger) or policy.max_calls != 250
        or grant['result_sha256'] != sha256(raw).hexdigest() or BLOCKED in ledger['calls']):
        raise ValueError('Inactive or mismatched Judge ceiling extension')
    retained_run_reservations(state, ledger)
    return True


def main() -> None:
    from frozen_budget_continuation import protected_tests
    from lobby_budget_period import period_usage
    from mixed_backend_policy import judge_policy
    from operational_transport import retained_run_reservations

    root = Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state = root / 'trusted-state'
    source = root / 'worktrees' / RUN / 'integration-v86'
    lease = RunLease(state, RUN, 'judge-ceiling-250-' + str(os.getpid()))
    lease.acquire(owner_alive=lambda _: True)
    try:
        raw = verify_stop(state, source)
        ledger = json.loads((run_path(state) / 'budget.json').read_bytes())
        period_usage(state, ledger)
        retained_run_reservations(state, ledger)
        protected_tests(state, source, 86)
        base = judge_policy()
        claims = claim_archive(state)
        if len(claims) != base.max_calls or base.max_calls != 200 or BLOCKED in ledger['calls']:
            raise ValueError('Expected the exact original Judge dispatch limit')
        policy = replace(base, max_calls=250, authorization_ref=REF)
        payload = {'authority': 'explicit_user_session', 'reply': REPLY, 'run': RUN,
                   'base_policy_sha256': base.sha256, 'policy_sha256': policy.sha256,
                   'result_sha256': sha256(raw).hexdigest(),
                   'history': {k: ledger[k] for k in ('calls', 'cycles', 'limits')} | {'claims': claims}}
        path = state / REF
        if path.exists():
            if json.loads(path.read_bytes()) != payload:
                raise ValueError('Preserve existing Judge extension authorization')
        else:
            atomic_write(state, REF, json.dumps(payload, sort_keys=True).encode())
        print(json.dumps({'retained_claims': len(claims), 'judge_ceiling': policy.max_calls,
                          'retained_charges': len(ledger['calls']), 'candidate': CANDIDATE}), flush=True)
    finally:
        lease.release()


if __name__ == '__main__':
    main()
