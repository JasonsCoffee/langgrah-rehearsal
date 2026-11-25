"""Explicit host budget periods preserve the cumulative native run ledger."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path

from unity_coder.core.ownership import confined_path

PERIOD = 'post-backend-20261123'
PREFIX = '.agent/runs/monopoly-game-lobby/'
EXTENSION_ID = 'post-backend-30m'
EXTENSION_REF = 'recovery-authorizations/post-backend-30m.json'
EXTENSION_REPLY = 'Approve 30M input; keep 2M output / 120 cycles'
EXTENSION_40_ID = 'post-backend-40m'
EXTENSION_40_REF = 'recovery-authorizations/post-backend-40m.json'
EXTENSION_40_REPLY = ('I see, now the implementation steps are getting more clear to me. '
                      'Your requirement of increasing the input budget is approved. '
                      'You can proceed to implement the next unit now.')

EXTENSION_50_ID = 'post-backend-50m'
EXTENSION_50_REF = 'recovery-authorizations/post-backend-50m.json'
EXTENSION_50_REPLY = 'ok. input budget is approved. continue your work.'
EXTENSION_70_ID = 'post-backend-70m'
EXTENSION_70_REF = 'recovery-authorizations/post-backend-70m.json'
EXTENSION_70_REPLY = ('Ok, method changes are approved. At the same time, '
                      'increase the input ceiling to 70M. Please continue.')
EXTENSION_90_ID = 'post-backend-90m'
EXTENSION_90_REF = 'recovery-authorizations/post-backend-90m.json'
EXTENSION_90_REPLY = 'Approve 90M input'
EXTENSION_110_ID = 'post-backend-110m'
EXTENSION_110_REF = 'recovery-authorizations/post-backend-110m.json'
EXTENSION_110_REPLY = 'Approve 110M input'




def _read_period(state: Path) -> tuple[dict, dict]:
    marker = json.loads((state / 'budget-periods/active.json').read_bytes())
    raw = confined_path(state, marker['record_ref']).read_bytes()
    if sha256(raw).hexdigest() != marker['record_sha256']:
        raise ValueError('Budget period identity changed')
    record = json.loads(raw)
    raw = confined_path(state, record['snapshot_ref']).read_bytes()
    if sha256(raw).hexdigest() != record['snapshot_sha256']:
        raise ValueError('Budget period history changed')
    return record, json.loads(raw)


def authorized_limits(state: Path, ledger: dict, limits: list[int], original: list[int]) -> list[int]:
    """Validate separate human budget authority without rewriting model grants."""
    if not (state / 'budget-periods/active.json').exists():
        if limits != original:
            raise ValueError('Matching original or explicit period authorization required')
        return original
    record, before = _read_period(state)
    baseline = [sum(c.get('actual', c['reserved'])[i] for c in before['calls'].values()) for i in range(2)]
    cycles = len(before['cycles'])
    expected = [baseline[0] + 20000000, baseline[1] + 2000000, cycles + 50, original[3]]
    if (ledger['limits'][1:] != expected[1:]
        or ledger['limits'][0] - expected[0] not in (0,10000000,20000000,30000000,50000000,70000000,90000000)):
        raise ValueError('Unrecognized period ceiling')
    for recovery_id, provenance, reply, increase in (
        (EXTENSION_ID, EXTENSION_REF, EXTENSION_REPLY, 10000000),
        (EXTENSION_40_ID, EXTENSION_40_REF, EXTENSION_40_REPLY, 10000000),
        (EXTENSION_50_ID, EXTENSION_50_REF, EXTENSION_50_REPLY, 10000000),
        (EXTENSION_70_ID, EXTENSION_70_REF, EXTENSION_70_REPLY, 20000000),
        (EXTENSION_90_ID, EXTENSION_90_REF, EXTENSION_90_REPLY, 20000000),
        (EXTENSION_110_ID, EXTENSION_110_REF, EXTENSION_110_REPLY, 20000000),
    ):
        if ledger['limits'][0] <= expected[0]:
            break
        expected = recovered_limits(state, ledger, expected, recovery_id=recovery_id,
                                    provenance=provenance, reply=reply, increase=increase)
    if (record.get('authority') != 'explicit_user_session'
        or record.get('run_id') != 'monopoly-game-lobby'
        or record.get('period_id') != PERIOD
        or record.get('allowance') != [20000000, 2000000, 50]
        or record.get('baseline_accounted') != baseline
        or record.get('baseline_cycles') != cycles
        or before['limits'] != original or ledger['limits'] != expected or limits != expected
        or any(ledger['calls'].get(k) != v for k, v in before['calls'].items())
        or any(ledger['cycles'].get(k) != v for k, v in before['cycles'].items())):
        raise ValueError('Budget period requires exact retained history and authorized allowance')
    return original


def recovered_limits(state: Path, ledger: dict, prior_limits: list[int], *,
                     recovery_id: str=EXTENSION_ID, provenance: str=EXTENSION_REF,
                     reply: str=EXTENSION_REPLY, increase: int=10000000) -> list[int]:
    """Recognize the extension only after a completed native budget recovery."""
    intent = json.loads((state / (PREFIX + 'recoveries/' + recovery_id + '.json')).read_bytes())
    approval = json.loads((state / provenance).read_bytes())
    grant = intent['authorization']
    before = json.loads(bytes.fromhex(intent['saved']['budget.json']))
    result_raw = bytes.fromhex(intent['saved']['result.json'])
    result = json.loads(result_raw)
    expected = [prior_limits[0] + increase, *prior_limits[1:]]
    after = intent['budget_after']
    if (intent['state'] != 'complete'
        or approval != {'authority':'explicit_user_session','reply':reply,'grant':grant}
        or grant['recovery_id'] != recovery_id or grant['provenance'] != provenance
        or grant['run_id'] != 'monopoly-game-lobby'
        or [grant['input_limit'], grant['output_limit'], grant['max_cycles']] != expected[:3]
        or grant['result_sha256'] != sha256(result_raw).hexdigest()
        or result['outcome'] != 'abandon' or result['reason'] != 'budget'
        or grant['previous_sha256'] != result['contract_sha256']
        or before['limits'] != prior_limits or after['limits'] != expected
        or before['calls'] != after['calls']
        or any(ledger['calls'].get(k) != v for k,v in after['calls'].items())
        or any(ledger['cycles'].get(k) != v for k,v in after['cycles'].items())):
        raise ValueError('30M extension requires the exact completed native recovery and retained history')
    return expected


def period_usage(state: Path, ledger: dict) -> tuple[list[int], int]:
    """Report this period independently of all historical usage and reservations."""
    record, before = _read_period(state)
    authorized_limits(state, ledger, ledger['limits'], before['limits'])
    new_calls = [c for k, c in ledger['calls'].items() if k not in before['calls']]
    return ([sum(c.get('actual', c['reserved'])[i] for c in new_calls) for i in range(2)],
            len(ledger['cycles']) - record['baseline_cycles'])


def apply_period(state: Path) -> dict:
    """Apply the user's one-time period amendment at the idle rework boundary."""
    from unity_coder.core.lifecycle import RunLease
    from unity_coder.core.storage import atomic_write, file_guard

    lease = RunLease(state, 'monopoly-game-lobby', 'budget-period-' + str(os.getpid()))
    lease.acquire(owner_alive=lambda _: True)
    try:
        with file_guard(state, PREFIX + 'budget.guard'):
            if (state / 'budget-periods/active.json').exists():
                raise ValueError('A period already exists; no reset or replay')
            original = (state / (PREFIX + 'budget.json')).read_bytes()
            before = json.loads(original)
            policy_raw = (state / 'budget-policy.json').read_bytes()
            policy = json.loads(policy_raw)
            result_raw = (state / (PREFIX + 'result.json')).read_bytes()
            result = json.loads(result_raw)
            if (before['limits'] != [250000000, 24000000, 160, 2]
                or len(before['cycles']) != 70 or before.get('stopped')
                or result.get('outcome') != 'rework' or result.get('contract_version') != 70
                or result.get('candidate_revision') != '625db77bf4e75060435947d955328a729f6f87dc'
                or [policy[k] for k in ('input_limit', 'output_limit', 'max_cycles', 'max_added_units')] != before['limits']):
                raise ValueError('Exact idle cycle-70 boundary and matching original policy required')
            folder = 'budget-periods/' + PERIOD + '/'
            if (state / folder).exists():
                raise ValueError('Preserve existing period preparation for explicit reconciliation')
            baseline = [sum(c.get('actual', c['reserved'])[i] for c in before['calls'].values()) for i in range(2)]
            settled = [sum(c['actual'][i] for c in before['calls'].values() if 'actual' in c) for i in range(2)]
            record = {'authority': 'explicit_user_session', 'run_id': 'monopoly-game-lobby',
                      'period_id': PERIOD, 'baseline_accounted': baseline, 'baseline_settled': settled,
                      'baseline_reserved': [baseline[i] - settled[i] for i in range(2)],
                      'baseline_cycles': 70, 'historical_calls': len(before['calls']),
                      'unknown_calls': [k for k, c in before['calls'].items() if 'actual' not in c],
                      'allowance': [20000000, 2000000, 50], 'snapshot_ref': folder + 'ledger.before.json',
                      'snapshot_sha256': sha256(original).hexdigest(), 'candidate': result['candidate_revision'],
                      'contract_sha256': result['contract_sha256'],
                      'authorization': 'User requested reset token usage to a new 20M input / 2M output period and 50-cycle ceiling, preserving current usage and cycles as working history.',
                      'history_policy': 'Prior unknown calls remain fully reserved; reconciling historical entries requires an explicit period amendment.',
                      'contract_numbering': 'Native versions remain consecutive; period cycle zero starts after native cycle 70.'}
            raw = json.dumps(record, indent=2, sort_keys=True).encode()
            for name, content in [('ledger.before.json', original), ('policy.before.json', policy_raw),
                                  ('result.before.json', result_raw), ('period.json', raw),
                                  ('backend.before.json', (state / 'model-authorizations/active-backend.json').read_bytes())]:
                atomic_write(state, folder + name, content)
            current = before | {'limits': [baseline[0] + 20000000, baseline[1] + 2000000, 120, 2]}
            updated_policy = policy | dict(zip(('input_limit', 'output_limit', 'max_cycles', 'max_added_units'), current['limits']))
            atomic_write(state, 'budget-periods/active.json', json.dumps({'record_ref': folder + 'period.json',
                'record_sha256': sha256(raw).hexdigest()}, sort_keys=True).encode())
            authorized_limits(state, current, current['limits'], before['limits'])
            atomic_write(state, 'budget-policy.json', json.dumps(updated_policy, indent=2).encode())
            atomic_write(state, PREFIX + 'budget.json', json.dumps(current, sort_keys=True).encode())
            assert period_usage(state, current) == ([0, 0], 0)
            receipt = {'state': 'complete', 'period_id': PERIOD, 'baseline_accounted': baseline,
                       'historical_cycles': 70, 'period_usage': [0, 0], 'period_cycles': 0,
                       'allowance': [20000000, 2000000, 50], 'cumulative_limits': current['limits'],
                       'preserved_calls': current['calls'] == before['calls'],
                       'preserved_cycles': current['cycles'] == before['cycles'], 'human_accepted': False}
            atomic_write(state, folder + 'applied.json', json.dumps(receipt, indent=2).encode())
            return receipt
    finally:
        lease.release()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply the one-time explicit user amendment')
    args = parser.parse_args()
    state = Path(os.environ['LOBBY_RUN_ROOT']).resolve() / 'trusted-state'
    if args.apply:
        report = apply_period(state)
    else:
        ledger = json.loads((state / (PREFIX + 'budget.json')).read_bytes())
        tokens, _ = period_usage(state, ledger)
        record, _ = _read_period(state)
        token_limits = [ledger['limits'][i] - record['baseline_accounted'][i] for i in range(2)]
        report = {'period_id': record['period_id'], 'period_usage': tokens,
                  'token_limits': token_limits,
                  'remaining': [token_limits[i] - tokens[i] for i in range(2)],
                  'contract_cycle': len(ledger['cycles']), 'cycle_ceiling': ledger['limits'][2],
                  'remaining_cycles': ledger['limits'][2] - len(ledger['cycles']),
                  'historical_accounted': record['baseline_accounted'],
                  'historical_cycles': record['baseline_cycles'], 'cumulative_limits': ledger['limits']}
    print(json.dumps(report, indent=2))
