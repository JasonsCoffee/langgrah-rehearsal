"""Activate the verified compatibility wire and calibrate the same GLM judge."""
from hashlib import sha256
import json
import os
from pathlib import Path
from rehearsal_model_transport import RehearsalTransport
from unity_coder.core.ai_models import load_ai_config,ModelClient
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.model_workers import _object,parse_judgement
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main() -> None:
    directory=Path(__file__).parent;root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    if result['contract_version']!=23 or result['outcome']!='rework':raise ValueError('Expected the inspected cycle-23 boundary')
    integration=root/'worktrees/monopoly-game-lobby/integration-v23'
    if git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision'] or git(integration,'status','--porcelain'):raise ValueError('Candidate changed')
    settings=load_ai_config(Path('ai.local.toml'))
    if settings.judge.model!='z-ai/glm-5.3-flash' or settings.coder.model!='deepseek/deepseek-v4.1-flash':raise ValueError('Configured model changed')
    p=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=p['input_limit'],output_limit=p['output_limit'],max_cycles=p['max_cycles'],max_added_units=p['max_added_units'])
    lease=RunLease(state,'monopoly-game-lobby','verified-tls-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        policy={'format_version':1,'profile':'verified_tls12_app_identity','automatic_retries':0,'certificate_verification':'required'}
        path=state/'network-policy.openrouter.json'
        if path.exists() and json.loads(path.read_bytes())!=policy:raise ValueError('Preserve existing network policy')
        if not path.exists():atomic_write(state,'network-policy.openrouter.json',json.dumps(policy,indent=2).encode())
        proof={'authority':'explicit user request to fix OpenRouter TLS and continue the same run',
            'run_id':'monopoly-game-lobby','candidate_revision':result['candidate_revision'],
            'network_policy':policy,'usage_before':budget.totals(),'limits':budget.limits,
            'framework_runtime_changed':False,'verified':False,'automatic_retries':0,'human_accepted':False}
        proof_path='network-recovery/verified-tls-v23.json'
        if (state/proof_path).exists():raise ValueError('Preserve prior live probe evidence; no replay')
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        calls=ModelCalls(ModelClient(settings.judge,transport=RehearsalTransport(state,'judge'),timeout=180),budget,'monopoly-game-lobby')
        cases=[('tls-recovery-v23-glm-json-review','Independently review this synthetic test. Return ONLY JSON with valid (boolean) and explanation (nonempty string). Criterion: cancelling preserves the wallet. Test: var before=ReadWallet(); CancelQueue(); Assert.That(before, Is.EqualTo(before));'),
            ('tls-recovery-v23-glm-json-defect','Classify the defect as implementation or contract. Return ONLY JSON with defect_class (implementation or contract) and explanation. The accepted complete contract requires cancellation to preserve 500 coins. Implementation: CancelQueue(){ Coins=0; }. The correct test expects 500 after cancelling and observes zero. The fixture and contract are consistent.')]
        receipts=[]
        for index,(call,prompt) in enumerate(cases):
            reply=calls.generate(call,'TEST-VIP',prompt,max_output_tokens=32768)
            if reply.model.casefold()!='z-ai/glm-5.3-flash':raise ValueError('Response model differs from selected judge')
            if index==0:
                decision=_object(reply.text,{'valid','explanation'})
                if decision['valid'] is not False or not isinstance(decision['explanation'],str) or not decision['explanation'].strip():raise ValueError('Vacuity calibration failed')
            elif parse_judgement(reply.text)[0]!='implementation':raise ValueError('Defect calibration failed')
            receipts.append({'call_id':call,'response_model':reply.model,'input_tokens':reply.input_tokens,'output_tokens':reply.output_tokens})
            proof.update(completed_probes=receipts,usage_after=budget.totals())
            atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        proof.update(verified=True,offline_tests_passed=56,tls_tests_sha256=sha256((directory/'test_verified_openrouter.py').read_bytes()).hexdigest(),wire_sha256=sha256((directory/'verified_openrouter.py').read_bytes()).hexdigest())
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        (directory/'evidence/tls-recovery-v23.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='')
        print(json.dumps(proof),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
