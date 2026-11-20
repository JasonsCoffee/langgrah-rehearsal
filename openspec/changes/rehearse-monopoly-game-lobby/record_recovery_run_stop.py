"""Record the actual final governor stop and full unchanged-host evidence."""
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
from overlay_host import OverlayHost
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
ledger=json.loads((run/'budget.json').read_bytes())
if result['outcome']!='abandon' or result['contract_version']!=6 or not ledger.get('stopped'):
    raise ValueError('Expected the actual final authorized cycle-budget stop')
source=root/'worktrees/monopoly-game-lobby/integration-v6'
branch=json.loads((run/'abandon-v6.json').read_bytes())
if (git(root/'module','rev-parse',branch['branch']).decode().strip()!=result['candidate_revision']
    or git(source,'rev-parse','HEAD').decode().strip()!=branch['restored_revision']
    or git(source,'status','--porcelain')):
    raise ValueError('Retained or restored candidate identity changed')
roles=Counter();models=set()
for receipt in (run/'model-calls').glob('*.json'):
    identity=json.loads(receipt.read_bytes())['identity'];roles[identity['role']]+=1;models.add(identity['model'])
used=[sum(c.get('actual',c['reserved'])[i] for c in ledger['calls'].values()) for i in (0,1)]
checkpoint=json.loads((run/'services-v6/state.json').read_bytes())
executor=json.loads((run/'executor-v6.json').read_bytes())
host=OverlayHost();host.lease.acquire(owner_alive=lambda _:True)
try:
    host.preflight()
    overlay=host.overlay.read()
    print('CHECK verifying all original host files and current preparation candidate',flush=True)
    host.overlay.assert_ready(overlay['candidate'])
finally:host.lease.release()
directory=Path(__file__).parent
expected={'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
          'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}
if any(sha256((directory/name).read_bytes()).hexdigest()!=digest for name,digest in expected.items()):
    raise ValueError('Trusted overlay code changed')
summary={'run_id':'monopoly-game-lobby','native_result':result,'retained_branch':branch['branch'],
    'restored_baseline':branch['restored_revision'],'limits':ledger['limits'],'used':used,
    'remaining_tokens':[ledger['limits'][i]-used[i] for i in (0,1)],'consumed_cycles':list(ledger['cycles']),
    'paid_calls':len(ledger['calls']),'unsettled_calls':sum('actual' not in c for c in ledger['calls'].values()),
    'calls_by_role':dict(roles),'models':sorted(models),'global_tests_frozen':checkpoint['tdd']['frozen'] is not None,
    'implementation_dispatched':any(s['stage']=='code' for s in executor['steps']),
    'selected_unity_tests_executed':0,'framework_recovery_tests_passed':23,'full_framework_tests_passed':526,
    'human_accepted':False,'awaiting_human_review':False,'trusted_overlay_unchanged':True,
    'preservation':{'full_original_file_check_passed':True,'original_files':len(overlay['baseline']),
        'baseline_sha256':overlay['baseline_sha256'],'materialized_preparation_candidate':overlay['candidate'],
        'pending_metadata':len(overlay['pending'])},
    'blocker':'The independent judge rejected the core UI acceptance suite after its three preparation attempts. The sixth contract cycle exhausted the explicitly amended cycle ceiling; tokens remain. Lifecycle exception suppression/no-op paths, shared formatter use, equipped rendering/animation and layout/pointer assertions remain incomplete. No global freeze, implementation dispatch or human-review offer occurred.'}
snapshot=state/'recovery-final-v6'
if snapshot.exists():raise ValueError('Preserve existing final snapshot; no implicit overwrite')
snapshot.mkdir()
for name in ('result.json','budget.json','dossier-v6.json','executor-v6.json','abandon-v6.json'):
    (snapshot/name).write_bytes((run/name).read_bytes())
for name in ('lobby_production_host.py','rehearsal_model_transport.py','scoped_context.py','token-policy.json','trusted_overlay.py','overlay_host.py'):
    (snapshot/name).write_bytes((directory/name).read_bytes())
atomic_write(state,'recovery-final-v6/summary.json',json.dumps(summary,ensure_ascii=False,indent=2).encode())
(directory/'evidence/recovery-final-v6.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
(directory/'evidence/dossier-v6.json').write_bytes((run/'dossier-v6.json').read_bytes())
print(json.dumps(summary,ensure_ascii=False),flush=True)
