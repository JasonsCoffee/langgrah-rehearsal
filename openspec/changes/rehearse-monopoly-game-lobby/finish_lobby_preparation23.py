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
from operational_transport import retained_transport_failure, retained_key_limit_failure

framework=Path.cwd().resolve()
root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework':raise ValueError('Only actual native rework may transition')
previous_version=result['contract_version'];version=previous_version+1
policy=json.loads((state/'budget-policy.json').read_bytes())
if version>policy['max_cycles']:raise ValueError('Authorized cycle ceiling reached')
dossier=json.loads((run/('dossier-v'+str(previous_version)+'.json')).read_bytes())
if previous_version!=22 or version!=23:raise ValueError('Only the inspected unpublished preparation may resume')
source=root/'worktrees/architect-v23'
if not source.is_dir():raise ValueError('Prepared worktree is missing')
if git(source,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']:raise ValueError('Prepared baseline changed')
if json.loads((run/'services-v22/state.json').read_bytes())['tdd']['frozen'] is not None:raise ValueError('Frozen test state changed')
spec=source/'specs/monopoly-game-lobby';current=json.loads((spec/'contract.v23.json').read_bytes())
for migration in current['ownership_migrations']:
    if migration['from_unit'] not in ('TEST-CARDS','TEST-SOCIAL'):raise ValueError('Unexpected migration')
    migration['paths']=[path for path in migration['paths'] if '.recovery-v4.md' in path]
    if len(migration['paths'])!=2:raise ValueError('Exactly the existing history note and metadata may migrate')
# Assert every existing delegated body is still byte-identical to partition proof.
from tree_sitter import Language,Parser
import tree_sitter_c_sharp
parser=Parser(Language(tree_sitter_c_sharp.language()))
proofs=json.loads((spec/'author-partitions.v23.json').read_bytes())
for proof in proofs:
    class_name='LobbyEconomyTests' if proof['from_unit']=='TEST-CARDS' else 'LobbySocialTests'
    names={}
    for path in source.glob('Tests/Runtime/Script/LobbyRehearsal/*.cs'):
        tree=parser.parse(path.read_bytes())
        if tree.root_node.has_error:raise ValueError('Prepared source parse changed')
        def visit(node):
            if node.type=='class_declaration' and node.child_by_field_name('name').text.decode()!=class_name:return
            if node.type=='method_declaration' and any(c.type=='attribute_list' and b'[Test]' in c.text for c in node.children):
                name=node.child_by_field_name('name').text.decode();names[name]=sha256(node.text).hexdigest()
            for child in node.children:visit(child)
        visit(tree.root_node)
    if any(names.get(name)!=digest for name,digest in proof['method_sha256'].items()):raise ValueError('An assertion body changed')
(spec/'contract.v23.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
rules=UnityAdapter();contracts=[]
for n in range(1,version+1):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=policy['max_cycles']))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
git(source,'add','specs/monopoly-game-lobby','Tests/Runtime/Script/LobbyRehearsal')
if version==10:git(source,'add','Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Prepare consecutive delegated test repair cycle '+str(version))
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework)
(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
def reconciled():
    ledger=json.loads((run/'budget.json').read_bytes())
    for call_id,call in ledger['calls'].items():
        if 'actual' in call:continue
        receipt=json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        if call_id=='v8-step3-prepare-review-TEST-PRES-CORE':retained_transport_failure(receipt,call,8)
        elif call_id=='v16-step1-prepare-review-TEST-APPEAR':retained_key_limit_failure(receipt,call,16)
        else:raise ValueError('Unreconciled paid operation')
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
