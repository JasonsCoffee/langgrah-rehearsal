"""Prepare and transition an actual consecutive native rework, preserving usage."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid5,NAMESPACE_URL
from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.architect_boundary import discover_context
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.contracts import load_contract
from unity_coder.core.cycles import transition_cycle
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.storage import atomic_write
from unity_coder.core.target_profiles import load_profile
from unity_coder.core.workspaces import git
from operational_transport import retained_run_reservations, retained_coder_request_failure, retained_coder_connection_failure, retained_sol_review_failure, retained_transport_failure, retained_key_limit_failure, retained_calibration_failure, retained_tls_probe_failure

framework=Path.cwd().resolve()
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework':raise ValueError('Only actual native rework may transition')
previous_version=result['contract_version'];version=previous_version+1
policy=json.loads((state/'budget-policy.json').read_bytes())
if version>policy['max_cycles']:raise ValueError('Authorized cycle ceiling reached')
dossier=json.loads((run/('dossier-v'+str(previous_version)+'.json')).read_bytes())
source=root/'worktrees'/('architect-v'+str(version))
if not source.exists():raise ValueError('Expected preserved prepared worktree')
if git(source,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']:raise ValueError('Unexpected prepared parent')
spec=source/'specs/monopoly-game-lobby'
current=json.loads((spec/'contract.v30.json').read_bytes())
proof=json.loads((spec/'author-partitions.v30.json').read_bytes())
if proof['counts']!=[10,5,4] or not proof['all_nineteen_method_bodies_byte_identical']:raise ValueError('Partition proof mismatch')
profile_path=source/current['coding_profile_ref']['path']
profile=json.loads(profile_path.read_bytes())
world='Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs'
old_profile=json.loads((source/'specs/monopoly-game-lobby/contract.v29.json').read_bytes())['coding_profile_ref']['path']
expected=json.loads((source/old_profile).read_bytes())
for ref in expected['rules']:
    if ref['path']==world:ref['sha256']=sha256((source/world).read_bytes()).hexdigest()
expected['protected_paths'] += ['Tests/Runtime/Script/LobbyRehearsal/'+name+'.cs.meta' for name in ('LobbySocialRequestsTests','LobbySocialPartnersTests')]
if {k:v for k,v in profile.items() if k!='rules'}!={k:v for k,v in expected.items() if k!='rules'}:raise ValueError('Unexpected profile changes')
profile_path.write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
current['coding_profile_ref']['sha256']=sha256(profile_path.read_bytes()).hexdigest()
(spec/'contract.v30.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter();contracts=[]
for n in range(1,version+1):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=policy['max_cycles']))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
git(source,'add','specs/monopoly-game-lobby','Tests/Runtime/Script/LobbyRehearsal','Runtime/Script/UI/LobbyRehearsal/LobbyWorld.cs')
if version==10:git(source,'add','Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare consecutive delegated test repair cycle '+str(version))
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
def reconciled():
    retained_run_reservations(state,json.loads((run/'budget.json').read_bytes()))
    transaction=json.loads((run/('services-v'+str(previous_version))/'effects/transaction.json').read_bytes())
    if not transaction.get('complete') or git(source,'status','--porcelain'):return False
    return True
lease=RunLease(state,'monopoly-game-lobby','cycle-transition-'+str(os.getpid()))
lease.acquire(owner_alive=lambda _:True)
try:
    transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
    candidate=git(source,'rev-parse','HEAD').decode().strip()
    active={'version':version,'candidate':candidate,'contract_source':'architect-v'+str(version),'contract_sha256':contracts[-1].sha256}
    atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
    print(json.dumps(active|{'preserved_usage':budget.totals(),'limits':budget.limits,'human_accepted':False}))
finally:lease.release()
