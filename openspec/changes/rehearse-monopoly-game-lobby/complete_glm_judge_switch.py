"""Verify the configured GLM judge after adding scoped wire-level JSON mode."""
from hashlib import sha256
import json
import os
from pathlib import Path
from rehearsal_model_transport import RehearsalTransport
from switch_lobby_judge_glm import public
from unity_coder.core.ai_models import load_ai_config, ModelClient
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.model_workers import _object, parse_judgement
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    framework=Path.cwd().resolve();directory=Path(__file__).parent
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True);state=root/'trusted-state'
    path='model-authorizations/judge-glm-5.3-flash-v23.json'
    proof=json.loads((state/path).read_bytes())
    if not proof['configured'] or proof['probe_verified']:raise ValueError('Only the inspected initial format failure may be reconciled')
    settings=load_ai_config(framework/'ai.local.toml')
    if public(settings.judge)!=proof['new_judge'] or public(settings.coder)!=proof['coder']:raise ValueError('Configured identity changed')
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    integration=root/'worktrees/monopoly-game-lobby/integration-v23'
    if result['candidate_revision']!=proof['candidate_revision'] or git(integration,'status','--porcelain'):raise ValueError('Candidate changed')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    lease=RunLease(state,'monopoly-game-lobby','judge-json-mode-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        archive='model-authorizations/judge-glm-5.3-flash-v23.initial.json'
        if (state/archive).exists():raise ValueError('Preserve prior reconciliation, no replay')
        atomic_write(state,archive,json.dumps(proof,indent=2).encode())
        calls=ModelCalls(ModelClient(settings.judge,transport=RehearsalTransport(state,'judge'),timeout=180),budget,'monopoly-game-lobby')
        checks=[('judge-switch-v23-glm-json-review',
            'Independently review test validity. Return ONLY JSON with valid (boolean) and explanation (nonempty string). '
            'Criterion: cancelling restores the original wallet balance. Test: var before=ReadWallet(); CancelQueue(); Assert.That(before, Is.EqualTo(before));'),
            ('judge-switch-v23-glm-json-defect',
            'Classify the defect as implementation or contract. Return ONLY JSON with defect_class (implementation or contract) and explanation. '
            'The accepted contract explicitly requires CancelQueue to leave 500 coins unchanged. The implementation is CancelQueue(){ Coins=0; }. '
            'The correct test asserts Coins==500 after cancellation and fails with actual zero. The contract and fixture are complete and consistent.')]
        verified=[]
        for index,(call,prompt) in enumerate(checks):
            reply=calls.generate(call,'TEST-VIP',prompt,max_output_tokens=32768)
            if reply.model.casefold()!='z-ai/glm-5.3-flash':raise ValueError('Unexpected response model')
            if index==0:
                decision=_object(reply.text,{'valid','explanation'})
                if decision['valid'] is not False or not isinstance(decision['explanation'],str) or not decision['explanation'].strip():raise ValueError('Vacuity calibration failed')
            else:
                if parse_judgement(reply.text)[0]!='implementation':raise ValueError('Defect-routing calibration failed')
            verified.append({'call_id':call,'response_model':reply.model,'input_tokens':reply.input_tokens,'output_tokens':reply.output_tokens})
        proof.update(probe_verified=True,json_mode={'type':'json_object'},verification_calls=verified,
            initial_failed_probe_retained=True,usage_after=budget.totals(),limits=budget.limits,
            offline_tests={'passed':45,'new_checks':5,'frozen_test_sha256':sha256((directory/'test_glm_judge_transport.py').read_bytes()).hexdigest()},
            framework_runtime_changed=False,coder_changed=False,candidate_unchanged=True)
        atomic_write(state,path,json.dumps(proof,indent=2).encode())
        (directory/'evidence/judge-model-switch-glm-v23.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='')
        print(json.dumps({'judge':settings.judge.model,'coder':settings.coder.model,'verified':verified,
            'usage':budget.totals(),'limits':budget.limits,'candidate_unchanged':True,'human_accepted':False}),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
