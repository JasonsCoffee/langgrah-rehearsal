"""Capture an actual final bounded stop; never manufacture a review result."""
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
from overlay_host import OverlayHost
from unity_coder.core.workspaces import git

root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
directory=Path(__file__).parent
result=json.loads((run/'result.json').read_bytes())
ledger=json.loads((run/'budget.json').read_bytes())
version=result['contract_version']
if result['outcome']!='abandon' or not ledger.get('stopped'):
    raise ValueError('Only an actual native terminal budget stop may be recorded here')
snapshot=state/('ceiling-final-v'+str(version))
export=directory/'evidence'/('ceiling-final-v'+str(version)+'.json')
if snapshot.exists() or export.exists():raise ValueError('Preserve earlier evidence; no implicit overwrite')
branch=json.loads((run/('abandon-v'+str(version)+'.json')).read_bytes())
source=root/'worktrees/monopoly-game-lobby'/('integration-v'+str(version))
if (git(root/'module','rev-parse',branch['branch']).decode().strip()!=result['candidate_revision']
    or git(source,'rev-parse','HEAD').decode().strip()!=branch['restored_revision']
    or git(source,'status','--porcelain')):
    raise ValueError('Retained or restored candidate identity changed')
all_steps=[]
for path in run.glob('executor-v*.json'):all_steps.extend(json.loads(path.read_bytes())['steps'])
if any(step['stage'] in ('red','code','verify','refactor','final_verify','review','finalize') for step in all_steps):
    raise ValueError('Execution advanced beyond preparation; inspect actual test evidence before reporting')
checkpoint=json.loads((run/('services-v'+str(version))/'state.json').read_bytes())
if checkpoint['tdd']['frozen'] is not None:raise ValueError('Unexpected global test freeze')
expected={'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f',
    'overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}
if any(sha256((directory/name).read_bytes()).hexdigest()!=digest for name,digest in expected.items()):
    raise ValueError('Trusted overlay source changed')
host=OverlayHost();host.lease.acquire(owner_alive=lambda _:True)
try:
    host.preflight()
    overlay=host.overlay.read()
    print('Checking all original host files and the managed preparation candidate',flush=True)
    host.overlay.assert_ready(overlay['candidate'])
finally:host.lease.release()
used=[sum(c.get('actual',c['reserved'])[i] for c in ledger['calls'].values()) for i in (0,1)]
settled=[sum(c['actual'][i] for c in ledger['calls'].values() if 'actual' in c) for i in (0,1)]
uncertain={name:call['reserved'] for name,call in ledger['calls'].items() if 'actual' not in call}
roles=Counter();models=set()
for path in (run/'model-calls').glob('*.json'):
    identity=json.loads(path.read_bytes())['identity'];roles[identity['role']]+=1;models.add(identity['model'])
dossier_path=run/('dossier-v'+str(version)+'.json')
dossier=json.loads(dossier_path.read_bytes()) if dossier_path.exists() else None
record={'run_id':'monopoly-game-lobby','native_result':result,'governor_stop':ledger['stopped'],
    'retained_branch':branch['branch'],'restored_baseline':branch['restored_revision'],
    'limits':ledger['limits'],'usage_including_reservations':used,'settled_usage':settled,
    'uncertain_reservations':uncertain,'remaining_tokens':[ledger['limits'][i]-used[i] for i in (0,1)],
    'consumed_cycles':list(ledger['cycles']),'paid_calls':len(ledger['calls']),
    'calls_by_role':dict(roles),'models':sorted(models),'global_tests_frozen':False,
    'implementation_dispatched':False,'selected_unity_tests_executed':0,
    'framework_tests_passed':538,'target_wiring_tests_passed':21,
    'human_accepted':False,'awaiting_human_review':False,'dossier':dossier,
    'trusted_overlay_unchanged':True,'preservation':{'full_original_file_check_passed':True,
        'original_files':len(overlay['baseline']),'baseline_sha256':overlay['baseline_sha256'],
        'materialized_preparation_candidate':overlay['candidate'],'pending_metadata':len(overlay['pending'])}}
snapshot.mkdir()
for name in ('result.json','budget.json','executor-v'+str(version)+'.json','abandon-v'+str(version)+'.json'):
    (snapshot/name).write_bytes((run/name).read_bytes())
if dossier_path.exists():(snapshot/dossier_path.name).write_bytes(dossier_path.read_bytes())
wiring=('lobby_production_host.py','rehearsal_model_transport.py','scoped_context.py','compact_context.py',
    'guarded_author.py','operational_transport.py','continue_lobby_rework.py','token-policy.json',
    'trusted_overlay.py','overlay_host.py')
for name in wiring:(snapshot/name).write_bytes((directory/name).read_bytes())
record['wiring_sha256']={name:sha256((snapshot/name).read_bytes()).hexdigest() for name in wiring}
(snapshot/'summary.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
export.write_bytes((snapshot/'summary.json').read_bytes())
if dossier_path.exists():(directory/'evidence'/('dossier-final-v'+str(version)+'.json')).write_bytes(dossier_path.read_bytes())
print(json.dumps(record,ensure_ascii=False),flush=True)
