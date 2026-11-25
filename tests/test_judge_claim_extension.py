"""An amended Judge ceiling retains the original claim and ledger history."""
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))

from judge_claim_extension import REF, REPLY, RUN, amended_policy
from mixed_backend_policy import judge_policy


@pytest.mark.parametrize('drift', [None, 'claim', 'charge', 'cycle', 'limits', 'input_growth', 'input_reduction'])
def test_extension_authenticates_preserved_history(tmp_path, monkeypatch, drift):
    base = judge_policy()
    amended = replace(base, max_calls=250, authorization_ref=REF)
    history = {
        'claims': {f'judge-{i}': {'claim': str(i), 'receipt': str(i)} for i in range(200)},
        'calls': {'judge-0': {'actual': [10, 2]}},
        'cycles': {'1': {'contract': 'a'}},
        'limits': [70_000_000, 2_000_000, 120, 2],
    }
    path = tmp_path / REF
    path.parent.mkdir()
    path.write_text(json.dumps({
        'authority': 'explicit_user_session', 'reply': REPLY, 'run': RUN,
        'base_policy_sha256': base.sha256, 'policy_sha256': amended.sha256,
        'history': history,
    }))
    ledger = {'calls': dict(history['calls']), 'cycles': dict(history['cycles']),
              'limits': list(history['limits'])}
    ledger['calls']['judge-200'] = {'actual': [10, 2]}
    claims = dict(history['claims']) | {'judge-200': {'claim': 'new', 'receipt': 'new'}}
    monkeypatch.setattr('judge_claim_extension.claim_archive', lambda _: claims)
    if drift == 'claim':
        claims.pop('judge-0')
    elif drift == 'charge':
        ledger['calls']['judge-0'] = {'actual': [1, 2]}
    elif drift == 'cycle':
        ledger['cycles'].pop('1')
    elif drift == 'limits':
        ledger['limits'][1] -= 1
    elif drift == 'input_growth':
        ledger['limits'][0] += 20_000_000
    elif drift == 'input_reduction':
        ledger['limits'][0] -= 1
    if drift in (None, 'input_growth'):
        assert amended_policy(tmp_path, base, ledger) == amended
    else:
        with pytest.raises(ValueError, match='exact retained history'):
            amended_policy(tmp_path, base, ledger)
