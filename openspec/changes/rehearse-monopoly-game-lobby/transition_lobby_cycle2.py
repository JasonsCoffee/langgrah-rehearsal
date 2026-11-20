"""Use the native same-run transition after the actual cycle-1 rework dossier."""
import json
import os
from pathlib import Path
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
from unity_coder.adapters.unity import UnityAdapter

framework=Path.cwd().resolve()
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
state=root/'trusted-state'
version=int(os.environ.get('LOBBY_TRANSITION_VERSION','2'))
if version not in (2,3):raise ValueError('Only the prepared consecutive cycles are supported')
source=root/'worktrees'/('architect-v'+str(version))
spec=source/'specs/monopoly-game-lobby'
rules=UnityAdapter()
previous=None
for number in range(1,version):
    previous=load_contract((spec/('contract.v'+str(number)+'.json')).read_bytes(),source,rules,previous=previous)
current=load_contract((spec/('contract.v'+str(version)+'.json')).read_bytes(),source,rules,previous=previous)
context=discover_context(framework,json.loads((framework/'.agent/lobby-apply.json').read_bytes()),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
policy=json.loads((state/'budget-policy.json').read_bytes())
budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
receipt=json.loads((state/'prepared-shell-compile.json').read_bytes())
candidate=git(source,'rev-parse','HEAD').decode().strip()
if receipt['candidate']!=candidate or not receipt['evidence']['compilation']['passed']:
    raise ValueError('Cycle-2 prepared signatures require the exact successful compile receipt')
def reconciled():
    ledger=budget._read()
    if any('actual' not in call for call in ledger['calls'].values()):
        raise ValueError('Uncertain paid usage prevents transition')
    if git(source,'status','--porcelain'):
        raise ValueError('Dirty Architect baseline prevents transition')
    return True
lease=RunLease(state,'monopoly-game-lobby','cycle2-transition-'+str(os.getpid()))
lease.acquire(owner_alive=lambda _:True)
try:
    transition_cycle(framework,state,'monopoly-game-lobby',previous,current,context,budget,lease,workers_reconciled=reconciled)
    active={'version':version,'candidate':candidate,'contract_source':'architect-v'+str(version),'contract_sha256':current.sha256}
    atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
    print('Transitioned same run to cycle',version,'retained usage',budget.totals(),'baseline',candidate)
finally:
    lease.release()
