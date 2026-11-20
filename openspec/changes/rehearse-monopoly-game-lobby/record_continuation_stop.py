"""Record the actual native cycle-budget stop and final unchanged-host proof."""
from hashlib import sha256
import json
import os
from pathlib import Path
from collections import Counter
from overlay_host import OverlayHost
from unity_coder.core.storage import atomic_write

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve()
state=root/'trusted-state'
run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
ledger=json.loads((run/'budget.json').read_bytes())
if result['outcome']!='abandon' or ledger.get('stopped',{}).get('reason')!='budget':
    raise ValueError('Expected actual native budget abandonment')
usage=[sum(call.get('actual',call['reserved'])[i] for call in ledger['calls'].values()) for i in (0,1)]
roles=Counter()
models=set()
for receipt in (run/'model-calls').glob('*.json'):
    identity=json.loads(receipt.read_bytes())['identity']
    roles[identity['role']]+=1
    models.add(identity['model'])
host=OverlayHost()
host.lease.acquire(owner_alive=lambda _:True)
try:
    host.preflight()
    value=host.overlay.read()
    host.overlay.assert_ready(value['candidate'])
    preserved={'baseline_sha256':value['baseline_sha256'],'original_files':len(value['baseline']),
        'materialized_candidate':value['candidate'],'full_byte_check_passed':True,'pending_metadata':len(value['pending'])}
finally:
    host.lease.release()
wiring=Path(__file__).parent
previous=json.loads((state/'host-wiring/operational-stop-v1/hashes.json').read_bytes())
overlay_unchanged=all(sha256((wiring/name).read_bytes()).hexdigest()==previous[name] for name in ('trusted_overlay.py','overlay_host.py'))
if not overlay_unchanged:raise ValueError('Trusted overlay changed unexpectedly')
summary={'run_id':'monopoly-game-lobby','native_result':result,'limits':ledger['limits'],'used':usage,
    'token_allowance_remaining':[ledger['limits'][i]-usage[i] for i in (0,1)],'cycle_versions':list(ledger['cycles']),
    'model_calls_by_role':dict(roles),'configured_model_identities':sorted(models),'trusted_overlay_unchanged':True,
    'framework_runtime_changed':False,'global_tests_frozen':False,'tests_executed':0,'implementation_dispatched':False,
    'human_accepted':False,'preservation':preserved,
    'blocker':'Native run abandoned after three contract preparation cycles; token ceilings were increased tenfold but the original three-cycle ceiling remained. BudgetLedger rejects stopped dispatch, resume_operational excludes abandon, and transition_cycle requires a completed rework outcome. No supported same-run budget-abandon resume exists in the unchanged runtime.'}
atomic_write(state,'continuation-stop-summary.json',json.dumps(summary,ensure_ascii=False,indent=2).encode())
evidence=wiring/'evidence'
(evidence/'continuation-stop.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
snapshot=state/'host-wiring/continuation-final'
snapshot.mkdir(exist_ok=False)
hashes={}
for name in ('lobby_production_host.py','rehearsal_model_transport.py','trusted_overlay.py','overlay_host.py','record_continuation_stop.py'):
    data=(wiring/name).read_bytes()
    (snapshot/name).write_bytes(data)
    hashes[name]=sha256(data).hexdigest()
(snapshot/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print(json.dumps({'outcome':result['outcome'],'used':usage,'remaining':summary['token_allowance_remaining'],'preserved':preserved,'overlay_unchanged':True}))
