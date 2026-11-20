"""Read-only host/candidate audit after the exact provider key-limit stop."""
from hashlib import sha256
import json
import os
from pathlib import Path
from overlay_host import OverlayHost
from operational_transport import retained_run_reservations
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.workspaces import git


def main():
    directory=Path(__file__).parent
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    if result['contract_version']!=51 or (result['outcome'],result['reason'])!=('operational','Model transport requires reconciliation'):
        raise ValueError('Only the inspected provider stop')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    retained=retained_run_reservations(state,json.loads((run/'budget.json').read_bytes()))
    cfg=sha256(Path('ai.local.toml').read_bytes()).hexdigest()
    if cfg!='476182925b729aaf0bcbff2628cc15fc87c5d07ad4624d1c49945b7354f0722f':
        raise ValueError('AI configuration changed')
    expected={'trusted_overlay.py':'851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f','overlay_host.py':'53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190'}
    if any(sha256((directory/name).read_bytes()).hexdigest()!=digest for name,digest in expected.items()):
        raise ValueError('Trusted overlay sources changed')
    integration=root/'worktrees/monopoly-game-lobby/integration-v51'
    if result['candidate_revision']!='a21e01720dacd61d3604adca068f0b7a50e8ce6c' or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain'):
        raise ValueError('Exact admitted candidate changed')
    services=json.loads((run/'services-v51/state.json').read_bytes())
    if services['tdd']['frozen'] is not None:raise ValueError('Unexpected global freeze')
    implementation_calls=[]
    for path in (run/'model-calls').glob('*.json'):
        identity=json.loads(path.read_bytes())['identity']
        if identity['role']=='coder' and identity['unit_id'] in ('SHELL','ECON','MATCH','SOCIAL','RECORDS'):
            implementation_calls.append(identity['call_id'])
    host=OverlayHost();host.lease.acquire(owner_alive=lambda _:True)
    try:
        host.preflight()
        overlay=host.overlay.read();host.overlay.assert_ready(overlay['candidate'])
        evidence={'contract_version':51,'contract_sha256':result['contract_sha256'],
            'candidate':result['candidate_revision'],'outcome':'operational','reason':'OpenRouter HTTP 403 openrouter_key_limit',
            'accounted_tokens':budget.totals(),'active_limits':budget.limits,
            'retained_uncertain_reservations':len(retained),'ai_config_sha256':cfg,
            'trusted_overlay_source_sha256':expected,'bridge_project_identity_verified':True,
            'bridge_protocol':1,'bridge_modes':['compile','tests'],
            'original_host_files_checked':len(overlay['baseline']),'baseline_sha256':overlay['baseline_sha256'],
            'baseline_and_import_drift_check_passed':True,'materialized_candidate':overlay['candidate'],
            'current_candidate_materialized':overlay['candidate']==result['candidate_revision'],
            'global_tests_frozen':False,'implementation_model_calls':len(implementation_calls),
            'selected_lobby_unity_executions':0,'human_accepted':False,
            'pending_requests':{'provider_allowance_restoration':True,'TEST-CARDS_low_effort':'unanswered; none remains active'}}
        (directory/'evidence/provider-stop-v51.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8',newline='')
        print(json.dumps(evidence),flush=True)
    finally:host.lease.release()


if __name__=='__main__':main()
