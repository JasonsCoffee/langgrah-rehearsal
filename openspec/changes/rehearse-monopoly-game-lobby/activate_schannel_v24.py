"""Activate a target-only verified wire and calibrate the unchanged Sol judge."""
from hashlib import sha256
import json
import os
from pathlib import Path
from rehearsal_model_transport import RehearsalTransport
from unity_coder.core.ai_models import load_ai_config,ModelClient,ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.lifecycle import RunLease
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def main():
    root=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True);state=root/'trusted-state'
    run=state/'.agent/runs/monopoly-game-lobby';result=json.loads((run/'result.json').read_bytes())
    integration=root/'worktrees/monopoly-game-lobby/integration-v24'
    config=load_ai_config(Path('ai.local.toml'))
    if (result['outcome']!='operational' or result['contract_version']!=24
        or result['candidate_revision']!='cd868e9603a5aaf74509dabcdaff15394a893cf4'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or config.judge.model!='openai/gpt-6.1-sol'
        or config.coder.model!='deepseek/deepseek-v4.1-flash'):
        raise ValueError('Inspected run or configured models changed')
    limits=json.loads((state/'budget-policy.json').read_bytes())
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=limits['input_limit'],output_limit=limits['output_limit'],max_cycles=limits['max_cycles'],max_added_units=limits['max_added_units'])
    lease=RunLease(state,'monopoly-game-lobby','schannel-'+str(os.getpid()));lease.acquire(owner_alive=lambda _:True)
    try:
        if (state/'network-policy.sol-schannel.json').exists():raise ValueError('Preserve existing activation; no replay')
        proof={'candidate':result['candidate_revision'],'contract_sha256':result['contract_sha256'],
            'diagnosis':'Public unauthenticated TLS 1.2/1.3 Python probes reproduced SSLEOFError before HTTP; Windows Schannel GET 200 and POST 401 passed. Direct Python later recovered intermittently.',
            'usage_before':budget.totals(),'models_config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
            'coder_unchanged':True,'no_system_proxy_change':True,'human_accepted':False,
            'frozen_new_wire_test_sha256':sha256(Path(__file__).with_name('test_schannel_openrouter.py').read_bytes()).hexdigest(),
            'calibration_verified':False}
        atomic_write(state,'network-recovery/sol-schannel-v24.json',json.dumps(proof,indent=2).encode())
        atomic_write(state,'network-policy.sol-schannel.json',json.dumps({
            'format_version':1,'profile':'verified_schannel_curl','automatic_retries':0,
            'certificate_verification':'required','revocation':'best_effort'},indent=2).encode())
        calls=ModelCalls(ModelClient(config.judge,transport=RehearsalTransport(state,'judge'),timeout=180),budget,'monopoly-game-lobby')
        try:
            reply=calls.generate('sol-schannel-v24-json-review','TEST-VIP',
                'Independently review test validity. Return ONLY JSON with valid (boolean) and explanation. Criterion: cancelling preserves the wallet. Test: var before=ReadWallet(); CancelQueue(); Assert.That(before, Is.EqualTo(before));',max_output_tokens=32768)
            decision=json.loads(reply.text)
            if decision.get('valid') is not False or not decision.get('explanation'):raise ValueError('Vacuity calibration failed')
            proof.update(calibration_verified=True,calibration_usage=[reply.input_tokens,reply.output_tokens])
        except (ModelError,ValueError) as error:proof['calibration_error']=str(error)
        proof['usage_after']=budget.totals()
        atomic_write(state,'network-recovery/sol-schannel-v24.json',json.dumps(proof,indent=2).encode())
        print(json.dumps(proof),flush=True)
    finally:lease.release()


if __name__=='__main__':main()
