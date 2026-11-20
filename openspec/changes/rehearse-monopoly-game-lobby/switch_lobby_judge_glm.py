"""Import the explicit judge-model amendment without resetting the run."""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from rehearsal_model_transport import RehearsalTransport
from unity_coder.core.ai_models import load_ai_config, ModelClient, ModelError, ModelConfig
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def public(config: ModelConfig) -> dict[str,object]:
    return {k:getattr(config,k) for k in ('role','model','provider','effort','temperature_mode','upstream_provider','max_output_tokens')}


def main() -> None:
    framework=Path.cwd().resolve();directory=Path(__file__).parent
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)
    state=root/'trusted-state';run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    if result['contract_version']!=23 or result['outcome']!='rework':
        raise ValueError('Only the inspected quiescent cycle-23 boundary is authorized here')
    integration=root/'worktrees/monopoly-game-lobby/integration-v23'
    if (git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain')
        or not json.loads((run/'services-v23/effects/transaction.json').read_bytes()).get('complete')):
        raise ValueError('Candidate or completed-effect identity changed')
    proof_path='model-authorizations/judge-glm-5.3-flash-v23.json'
    if (state/proof_path).exists():
        raise ValueError('Preserve the existing amendment; do not replay its probe')
    policy=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=policy['input_limit'],output_limit=policy['output_limit'],max_cycles=policy['max_cycles'],max_added_units=policy['max_added_units'])
    lease=RunLease(state,'monopoly-game-lobby','judge-switch-'+str(os.getpid()))
    lease.acquire(owner_alive=lambda _:True)
    try:
        before=load_ai_config(framework/'ai.local.toml')
        if before.judge.model!='openai/gpt-6-astra':raise ValueError('Unexpected previous configured judge')
        old_raw=(framework/'ai.local.toml').read_bytes()
        text=old_raw.decode('utf-8-sig')
        match=re.search(r'(?ms)^\[judge\][^\r\n]*\r?\n(?P<section>.*?)(?=^\[|\Z)',text)
        if match is None:raise ValueError('Judge section missing')
        section,count=re.subn(r'(?m)^(\s*model\s*=\s*)["\']openai/gpt-6-astra["\']',r'\1"z-ai/glm-5.3-flash"',match['section'])
        if count!=1:raise ValueError('Expected exactly one judge-model assignment')
        new_text=text[:match.start('section')]+section+text[match.end('section'):]
        new_raw=(b'\xef\xbb\xbf' if old_raw.startswith(b'\xef\xbb\xbf') else b'')+new_text.encode('utf-8')
        accounting_before=budget.totals()
        proof={'authority':'explicit user request in active session',
            'request':'Please switch the judge to use glm-5.3-flash',
            'run_id':'monopoly-game-lobby','contract_version':23,'contract_sha256':result['contract_sha256'],
            'candidate_revision':result['candidate_revision'],'coder':public(before.coder),
            'old_judge':public(before.judge),'new_judge':public(replace(before.judge,model='z-ai/glm-5.3-flash')),
            'config_before_sha256':sha256(old_raw).hexdigest(),'config_after_sha256':sha256(new_raw).hexdigest(),
            'usage_before':accounting_before,'limits':budget.limits,'human_acceptance_granted':False,
            'provider_fallbacks':False,'configured':False,'probe_verified':False}
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        atomic_write(framework,'ai.local.toml',new_raw)
        after=load_ai_config(framework/'ai.local.toml')
        if after.coder!=before.coder or after.judge!=replace(before.judge,model='z-ai/glm-5.3-flash'):
            raise ValueError('An unrequested configuration field changed')
        proof['configured']=True;atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        call_id='judge-model-switch-v23-glm-5-3-flash-calibration'
        prompt=('Independently assess this synthetic test for behavioral validity. This is a calibration, '
            'not a lobby verdict or human acceptance. Require an assertion that can detect the specified defect. '
            'Return ONLY JSON with valid (boolean) and explanation (nonempty string).\n'
            'Criterion: cancelling a queue restores the original wallet balance. '
            'Test source: [Test] public void CancellingPreservesBalance() { var balance = ReadWallet(); '
            'CancelQueue(); Assert.That(balance, Is.EqualTo(balance)); }')
        calls=ModelCalls(ModelClient(after.judge,transport=RehearsalTransport(state,'judge'),timeout=180),budget,'monopoly-game-lobby')
        try:
            reply=calls.generate(call_id,'TEST-VIP',prompt,max_output_tokens=32768)
            decision=json.loads(reply.text)
            if decision.get('valid') is not False or not isinstance(decision.get('explanation'),str) or not decision['explanation'].strip():
                raise ValueError('Judge calibration failed to reject the deliberate self-comparison')
            if not reply.model.casefold().endswith('glm-5.3-flash'):
                raise ValueError('Unexpected response model; no automatic substitution')
            proof.update(probe_verified=True,probe_call=call_id,response_model=reply.model,
                calibration='Rejected an intentionally vacuous wallet assertion using valid structured JSON',
                usage_after=budget.totals())
        except (ModelError,ValueError) as error:
            proof.update(probe_call=call_id,probe_error=str(error),usage_after=budget.totals())
            atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
            raise
        atomic_write(state,proof_path,json.dumps(proof,indent=2).encode())
        (directory/'evidence/judge-model-switch-glm-v23.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='')
        print(json.dumps({'judge':after.judge.model,'coder':after.coder.model,'probe_verified':True,
            'probe_usage':[reply.input_tokens,reply.output_tokens],'preserved_usage':budget.totals(),
            'limits':budget.limits,'candidate_unchanged':True,'human_accepted':False}),flush=True)
    finally:
        lease.release()


if __name__=='__main__':main()
