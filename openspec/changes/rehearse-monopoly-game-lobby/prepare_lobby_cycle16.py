"""Reconcile actual compiler evidence, explicit catalog scope and D-26 review."""
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
from operational_transport import retained_transport_failure

framework=Path.cwd().resolve();directory=Path(__file__).parent;root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
if result['outcome']!='rework' or result['contract_version']!=15:raise ValueError('Actual version-fifteen rework required')
if json.loads((run/'services-v15/state.json').read_bytes())['tdd']['frozen'] is not None:raise ValueError('Never revise globally frozen tests')
diagnostic=json.loads((state/'compile-diagnostic-after-v15/complete.json').read_bytes())
if diagnostic['retained_candidate']!=result['candidate_revision'] or not diagnostic['budget_unchanged']:raise ValueError('Diagnostic identity changed')
source=root/'worktrees/architect-v16'
if source.exists():raise ValueError('Preserve existing preparation')
git(root/'module','merge-base','--is-ancestor',result['candidate_revision'],diagnostic['diagnostic_candidate'])
git(root/'module','worktree','add','-b','codex/lobby-architect-v16',str(source),diagnostic['diagnostic_candidate'])
spec=source/'specs/monopoly-game-lobby';old_path=spec/'contract.v15.json';old=json.loads(old_path.read_bytes())
current=old|{'contract_version':16,'previous_contract_sha256':sha256(old_path.read_bytes()).hexdigest(),'ownership_migrations':[]}
rules=UnityAdapter();owners={p:u['id'] for u in current['units'] if u['status']=='active' for p in u['owns']}
errors={}
for violation in diagnostic['compile_receipt']['evidence']['compilation']['violations']:
    path=violation['file'].removeprefix('Assets/JJGame/monopoly/')
    if path not in owners:raise ValueError('Compiler error outside declared ownership requires separate diagnosis')
    errors.setdefault(owners[path],[]).append(violation)
for name in ('approved-rehearsal-scope.v16.md','verification-strategy.v16.md','review-rubric.v16.json'):(spec/name).write_bytes((directory/name).read_bytes())
(spec/'mechanical-compile-errors.v16.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
conditions=json.loads((spec/'acceptance-conditions.v15.json').read_bytes())
visual={'US-L3-02':['V1'],'US-L3-03':['V2'],'US-L7-03':['V1'],'US-L7-10':['V3']}
for row in conditions:
    if row['story'] in visual:row['verification_allocation']={'automated':'Retain functional interactions, exact state/data, visibility/geometry and lifecycle assertions; see verification-strategy.v16.md.','candidate_bound_human_visual':visual[row['story']],'authority':'Frozen framework D-26; visual fidelity remains pending human acceptance.'}
    if row['story']=='US-L7-11':row['approved_rehearsal_disposition']='User explicitly approved Use rehearsal catalog; defer production integration. Verify complete catalog fields, exact products/prices and one shared data source for Appearance and Shop. Production Luban registration/generation and AssetGraph packaging are deferred and must not be claimed executed.'
(spec/'acceptance-conditions.v16.json').write_text(json.dumps(conditions,ensure_ascii=False,indent=2),encoding='utf-8',newline='')
finding=json.loads((run/'dossier-v15.json').read_bytes())['failed_units'][0]['hypothesis']
repair_ids=set(errors)|{'TEST-APPEAR'}
for unit in current['units']:
    if unit['id'] not in repair_ids:continue
    if unit['role']!='test':raise ValueError('Unexpected production compile defect')
    note=next(p for p in unit['owns'] if p.endswith('.cs')).removesuffix('.cs')+'.repair-v16.md'
    unit['owns'] += [note,note+'.meta'];guid=uuid5(NAMESPACE_URL,'monopoly-game-lobby/'+note).hex
    if unit['id']=='TEST-APPEAR':
        unit['instructions']='Repair the existing 23 mapped L3/L7/Journey_ECON tests, preserving effective functional assertions, exact IDs and partial-class identity. Latest real findings: '+finding+' Apply the explicit user catalog disposition in approved-rehearsal-scope.v16.md and the D-26 automated/human allocation in verification-strategy.v16.md. Do not claim pending V1/V2/V3 pixel/qualitative checks as automated passes. Replace the dossier-proven unreliable pixel-sampling assertions with sound functional/state/geometry observations and explicit candidate-bound review mappings; preserve all valid interaction, rendering-identity, visibility, transaction, persistence and lifecycle assertions. Fix active/visible selection and using markers and adversarial per-gender defaults with eligibility checks for every arranged account. Catalog fields and shared data provenance remain automated; production Luban/AssetGraph is explicitly deferred. Use the supported hash-bound edit transport. Update the clause-level acceptance map truthfully. Do not write game implementation or another unit partial file.'
    else:
        unit['instructions']+=' Cycle 16: prioritize the actual compiler errors in mechanical-compile-errors.v16.json for this unit. Preserve every effective mapped assertion and current public APIs. The CARDS partial must adapt to the actual read-only shared fixture helpers rather than restore obsolete Run/Activate helpers or synchronously consume async entry. Fully qualify ambiguous framework/game types in NFR without changing its prior valid behavior. Test source is not globally frozen; all source changes remain delegated.'
    unit['instructions']+=' Also write '+note+' and '+note+'.meta exactly fileFormatVersion: 2 newline guid: '+guid+' newline. Preserve historical notes. No disabled tests or fake coverage.'
next(u for u in current['units'] if u['id']=='SHELL')['instructions']+=' Implement all original visual behaviors; verification-strategy.v16.md assigns qualitative fidelity to the exact candidate human gate under D-26, not to omission of implementation. review-rubric.v16.json remains pending human acceptance. Production Luban/AssetGraph integration is explicitly deferred; use the prepared shared game-owned catalog.'
def ref(path):return {'path':path,'sha256':sha256((source/path).read_bytes()).hexdigest()}
profile=json.loads((source/old['coding_profile_ref']['path']).read_bytes())
new_rules=['specs/monopoly-game-lobby/'+name for name in ('approved-rehearsal-scope.v16.md','verification-strategy.v16.md','review-rubric.v16.json','mechanical-compile-errors.v16.json')]
profile['rules'] += [ref(path) for path in new_rules]
profile['protected_paths']=list(dict.fromkeys(profile['protected_paths']+new_rules+['specs/monopoly-game-lobby/acceptance-conditions.v16.json']))
(spec/'coding-profile.v16.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8',newline='');current['coding_profile_ref']=ref('specs/monopoly-game-lobby/coding-profile.v16.json')
for name in ('proposal.md','design.md'):(spec/name).write_bytes((directory/name).read_bytes())
(spec/'contract.v16.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
contracts=[]
for n in range(1,17):contracts.append(load_contract((spec/('contract.v'+str(n)+'.json')).read_bytes(),source,rules,previous=contracts[-1] if contracts else None,max_cycles=30))
load_profile((source/current['coding_profile_ref']['path']).read_bytes(),source,rules=rules,allowed_mount='Assets/JJGame/monopoly',implementation_roots=('Runtime/Script',),test_roots=('Tests/Runtime/Script/LobbyRehearsal',)).validate_contract(contracts[-1])
git(source,'add','specs/monopoly-game-lobby')
git(source,'-c','user.name=Lobby Rehearsal','-c','user.email=rehearsal@example.invalid','commit','-m','Reconcile compiler evidence, explicit catalog scope and candidate visual review')
raw=subprocess.check_output(['pnpm.cmd','exec','openspec','instructions','apply','--change','rehearse-monopoly-game-lobby','--json'],cwd=framework);(framework/'.agent/lobby-apply.json').write_bytes(raw)
context=discover_context(framework,json.loads(raw),sources=json.loads((framework/'.agent/lobby-sources.json').read_bytes()))
policy=json.loads((state/'budget-policy.json').read_bytes());budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
def reconciled():
    for call_id,call in json.loads((run/'budget.json').read_bytes())['calls'].items():
        if 'actual' in call:continue
        if call_id!='v8-step3-prepare-review-TEST-PRES-CORE':return False
        retained_transport_failure(json.loads((run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()),call,8)
    return json.loads((run/'services-v15/effects/transaction.json').read_bytes()).get('complete') is True and not git(source,'status','--porcelain')
lease=RunLease(state,'monopoly-game-lobby','cycle16-transition-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
try:
    atomic_write(state,'recovery-authorizations/catalog-scope-v16.json',json.dumps({'authority':'explicit user reply in active session','answer':'Use rehearsal catalog; defer production integration','source':'US-L7-11','human_acceptance_granted':False},indent=2).encode())
    transition_cycle(framework,state,'monopoly-game-lobby',contracts[-2],contracts[-1],context,budget,lease,workers_reconciled=reconciled)
    active={'version':16,'candidate':git(source,'rev-parse','HEAD').decode().strip(),'contract_source':'architect-v16','contract_sha256':contracts[-1].sha256}
    atomic_write(state,'current-execution.json',json.dumps(active,indent=2).encode())
    print(json.dumps(active|{'preserved_usage':budget.totals(),'limits':budget.limits,'compiler_errors_by_unit':{u:len(v) for u,v in errors.items()},'test_ids':len(current['test_links'])}))
finally:lease.release()
