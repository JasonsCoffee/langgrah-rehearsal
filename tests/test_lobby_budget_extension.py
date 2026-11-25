"""Only completed native recovery admits a higher period ceiling."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest

from test_lobby_budget_period import setup_period


@pytest.mark.parametrize('damage', [None, 'pending', 'lost_charge', 'approval'])
def test_native_extension_retains_accounting(tmp_path, damage):
    from lobby_budget_period import EXTENSION_ID, EXTENSION_REF, EXTENSION_REPLY, PREFIX, period_usage

    _, prior = setup_period(tmp_path)
    prior['calls']['period-call'] = {'unit':'A','version':1,'reserved':[20,10]}
    after = deepcopy(prior)
    after['limits'][0] += 10000000
    outcome = json.dumps({'outcome':'abandon','reason':'budget','contract_sha256':'contract'}).encode()
    grant = {'recovery_id':EXTENSION_ID,'provenance':EXTENSION_REF,'run_id':'monopoly-game-lobby',
             'input_limit':after['limits'][0],'output_limit':after['limits'][1],
             'max_cycles':after['limits'][2],'previous_sha256':'contract',
             'result_sha256':sha256(outcome).hexdigest()}
    intent = {'state':'pending' if damage=='pending' else 'complete','authorization':grant,
              'saved':{'budget.json':json.dumps(prior).encode().hex(),'result.json':outcome.hex()},
              'budget_after':after}
    for path, value in (
        (PREFIX+'recoveries/'+EXTENSION_ID+'.json',intent),
        (EXTENSION_REF,{'authority':'explicit_user_session',
                        'reply':'edited' if damage=='approval' else EXTENSION_REPLY,'grant':grant}),
    ):
        target = tmp_path/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(value),encoding='utf-8')
    ledger = deepcopy(after)
    if damage == 'lost_charge':
        del ledger['calls']['period-call']
    if damage:
        with pytest.raises(ValueError):
            period_usage(tmp_path,ledger)
    else:
        assert period_usage(tmp_path,ledger) == ([20,10],0)
