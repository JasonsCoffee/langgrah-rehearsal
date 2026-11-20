"""Apply the user's explicit tenfold token-budget amendment without resetting usage."""
from hashlib import sha256
import json
import os
from pathlib import Path
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write, file_guard

state=Path(os.environ['LOBBY_RUN_ROOT']).resolve()/'trusted-state'
prefix='.agent/runs/monopoly-game-lobby/'
lease=RunLease(state,'monopoly-game-lobby','authorized-budget-amendment-'+str(os.getpid()))
lease.acquire(owner_alive=lambda _:True)
try:
    with file_guard(state,prefix+'budget.guard'):
        original_policy=(state/'budget-policy.json').read_bytes()
        original_ledger=(state/(prefix+'budget.json')).read_bytes()
        policy=json.loads(original_policy)
        ledger=json.loads(original_ledger)
        if ledger['limits']==[3000000,900000,3,2] and policy['input_limit']==3000000 and policy['output_limit']==900000:
            print('Already amended; usage and cycle history retained')
        else:
            if ledger['limits']!=[300000,90000,3,2] or policy['input_limit']!=300000 or policy['output_limit']!=90000:
                raise ValueError('Unexpected original policy; no inferred budget reset')
            folder=state/'budget-amendments/tenfold-20261119'
            folder.mkdir(parents=True,exist_ok=False)
            (folder/'policy.before.json').write_bytes(original_policy)
            (folder/'ledger.before.json').write_bytes(original_ledger)
            policy.update(input_limit=3000000,output_limit=900000)
            ledger['limits']=[3000000,900000,3,2]
            record={'authorization':'User requested: Increase the budget to 10 times; continue the same run with configured models, trusted overlay and framework runtime unchanged.',
                'old_limits':[300000,90000,3,2],'new_limits':ledger['limits'],
                'old_policy_sha256':sha256(original_policy).hexdigest(),'old_ledger_sha256':sha256(original_ledger).hexdigest(),
                'retained_calls':ledger['calls'],'retained_cycles':ledger['cycles'],'usage_reset':False}
            atomic_write(state,'budget-amendments/tenfold-20261119/authorization.json',json.dumps(record,indent=2).encode())
            atomic_write(state,'budget-policy.json',json.dumps(policy,indent=2).encode())
            atomic_write(state,prefix+'budget.json',json.dumps(ledger,sort_keys=True).encode())
            print('Amended to 3,000,000 input / 900,000 output; retained all paid calls and cycle history; cycle/add-unit limits unchanged')
finally:
    lease.release()
