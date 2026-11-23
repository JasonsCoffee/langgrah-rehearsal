"""Fresh allowance retains run identities and uncertain historical charges."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def setup_period(root):
    before = {'limits': [250000000, 24000000, 160, 2],
              'cycles': {'1': {'sha256': 'contract', 'lineages': {'A': ['A']}}},
              'calls': {'old': {'unit': 'A', 'version': 1, 'reserved': [100, 50]}}}
    folder = root / 'budget-periods/post-backend-20261123'
    folder.mkdir(parents=True)
    raw = json.dumps(before).encode()
    (folder / 'ledger.before.json').write_bytes(raw)
    record = {'authority': 'explicit_user_session', 'run_id': 'monopoly-game-lobby',
              'period_id': 'post-backend-20261123', 'baseline_accounted': [100, 50],
              'baseline_cycles': 1, 'allowance': [20000000, 2000000, 50],
              'snapshot_ref': 'budget-periods/post-backend-20261123/ledger.before.json',
              'snapshot_sha256': sha256(raw).hexdigest()}
    raw = json.dumps(record).encode()
    (folder / 'period.json').write_bytes(raw)
    (root / 'budget-periods/active.json').write_text(json.dumps({
        'record_ref': 'budget-periods/post-backend-20261123/period.json',
        'record_sha256': sha256(raw).hexdigest()}))
    current = deepcopy(before)
    current['limits'] = [20000100, 2000050, 51, 2]
    return before, current


def test_period_starts_at_zero_without_removing_unknown_call(tmp_path):
    from lobby_budget_period import authorized_limits, period_usage
    before, current = setup_period(tmp_path)
    assert authorized_limits(tmp_path, current, current['limits'], before['limits']) == before['limits']
    assert period_usage(tmp_path, current) == ([0, 0], 0)
    assert current['calls'] == before['calls']


def test_new_calls_and_consecutive_cycles_count_only_in_new_period(tmp_path):
    from lobby_budget_period import period_usage
    _, current = setup_period(tmp_path)
    current['calls']['new'] = {'unit': 'A', 'version': 2, 'reserved': [70, 20], 'actual': [60, 10]}
    current['cycles']['2'] = {'sha256': 'next', 'lineages': {'A': ['A']}}
    assert period_usage(tmp_path, current) == ([60, 10], 1)


@pytest.mark.parametrize('damage', ['removed_call', 'changed_call', 'changed_cycle', 'raised_limit', 'snapshot'])
def test_period_rejects_history_and_policy_drift(tmp_path, damage):
    from lobby_budget_period import authorized_limits
    before, current = setup_period(tmp_path)
    if damage == 'removed_call': current['calls'].clear()
    if damage == 'changed_call': current['calls']['old']['actual'] = [1, 1]
    if damage == 'changed_cycle': current['cycles']['1']['sha256'] = 'other'
    if damage == 'raised_limit': current['limits'][0] += 1
    if damage == 'snapshot': (tmp_path / 'budget-periods/post-backend-20261123/ledger.before.json').write_text('{}')
    with pytest.raises(ValueError):
        authorized_limits(tmp_path, current, current['limits'], before['limits'])


def test_original_limits_cannot_bypass_active_period(tmp_path):
    from lobby_budget_period import authorized_limits
    before, current = setup_period(tmp_path)
    with pytest.raises(ValueError):
        authorized_limits(tmp_path, current, before['limits'], before['limits'])


def test_native_ledger_enforces_new_allowance_and_cycle_ceiling(tmp_path):
    from unity_coder.core.budget import BudgetLedger, BudgetExhausted
    _, current = setup_period(tmp_path)
    run = tmp_path / '.agent/runs/monopoly-game-lobby'
    run.mkdir(parents=True)
    (run / 'budget.json').write_text(json.dumps(current))
    ledger = BudgetLedger(tmp_path, 'monopoly-game-lobby', input_limit=20000100,
                          output_limit=2000050, max_cycles=51, max_added_units=2)
    ledger.reserve('full', 'A', 20000000, 2000000)
    with pytest.raises(BudgetExhausted): ledger.reserve('extra', 'A', 1, 0)
    for version in range(2, 52): ledger.begin_cycle(version, str(version), {'A': ('A',)})
    with pytest.raises(ValueError): ledger.begin_cycle(52, '52', {'A': ('A',)})
