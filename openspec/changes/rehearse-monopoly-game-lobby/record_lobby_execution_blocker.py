"""Record real native terminal evidence and recheck preservation; no paid calls."""
from hashlib import sha256
import json
import os
from pathlib import Path
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
from overlay_host import OverlayHost

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
state=root/'trusted-state'
module=root/'module'
run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='operational':
    raise ValueError('Expected the actual native operational result')
calls=[]
for path in sorted((run/'model-calls').glob('*.json')):
    record=json.loads(path.read_bytes())
    identity=record['identity']
    failure=record.get('failure',{})
    if 'reply' in record or failure.get('finish_reason')!='length':
        raise ValueError('Unexpected model receipt; reevaluate the blocker')
    calls.append({key:identity[key] for key in ('call_id','unit_id','model','role','output_limit')} |
                 {key:failure[key] for key in ('input_tokens','output_tokens','finish_reason')})
policy=json.loads((state/'budget-policy.json').read_bytes())
budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
usage=budget.totals()
if len(calls)!=3 or usage!=(59567,52000):
    raise ValueError('Actual receipts differ from the inspected three known failures')
host=OverlayHost()
host.lease.acquire(owner_alive=lambda _:True)
try:
    host.preflight()
    overlay=host.overlay.read()
    host.overlay.assert_ready(overlay['candidate'])
    preserved={'baseline_sha256':overlay['baseline_sha256'],'original_files':len(overlay['baseline']),
               'materialized_candidate':overlay['candidate'],'full_byte_check_passed':True,'pending_metadata':len(overlay['pending'])}
    atomic_write(state,'final-preservation-check.json',json.dumps(preserved,indent=2).encode())
finally:
    host.lease.release()
summary={'run_id':'monopoly-game-lobby','native_result':result,'module_baseline':git(module,'rev-parse','HEAD').decode().strip(),
    'contract_sha256':result['contract_sha256'],'model_calls':calls,'input_tokens_used':usage[0],'output_tokens_used':usage[1],
    'input_tokens_remaining':policy['input_limit']-usage[0],'output_tokens_remaining':policy['output_limit']-usage[1],
    'budget_reset':False,'model_substitution':False,'judge_calls':0,'tests_executed':0,'global_tests_frozen':False,
    'implementation_dispatched':False,'human_accepted':False,'preservation':preserved,
    'blocker':'Configured coder returned finish_reason length at all three bounded allowances without a complete content patch. Native worker intent has no usable result; test review/Red/freeze and implementation cannot proceed from these replies.'}
atomic_write(state,'execution-blocker-summary.json',json.dumps(summary,ensure_ascii=False,indent=2).encode())
evidence=Path(__file__).parent/'evidence'
evidence.mkdir(exist_ok=True)
(evidence/'execution-blocker.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
wiring=state/'host-wiring/operational-stop-v1'
wiring.mkdir(exist_ok=False)
hashes={}
for name in ('trusted_overlay.py','overlay_host.py','lobby_production_host.py','record_lobby_execution_blocker.py'):
    data=(Path(__file__).parent/name).read_bytes()
    (wiring/name).write_bytes(data)
    hashes[name]=sha256(data).hexdigest()
(wiring/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print(json.dumps({'outcome':result['outcome'],'usage':usage,'preservation':preserved,'human_accepted':False}))
