"""Publish an explicit next-request operator setting, without editing run journals."""
from hashlib import sha256
import json
import os
from pathlib import Path
from unity_coder.core.ai_models import load_ai_config
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.storage import atomic_write,file_guard


def main() -> None:
    state=Path(os.environ['LOBBY_RUN_ROOT']).resolve(strict=True)/'trusted-state'
    config=load_ai_config(Path('ai.local.toml'))
    config_hash=sha256(Path('ai.local.toml').read_bytes()).hexdigest()
    if (config_hash!='476182925b729aaf0bcbff2628cc15fc87c5d07ad4624d1c49945b7354f0722f'
        or config.coder.model!='deepseek/deepseek-v4.1-flash' or config.coder.effort
        or config.coder.upstream_provider!='alibaba' or config.coder.temperature_mode!='zero'
        or config.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Configured model policy changed; no activation')
    limits=json.loads((state/'budget-policy.json').read_bytes())
    if limits['run_id']!='monopoly-game-lobby':raise ValueError('Run changed')
    budget=BudgetLedger(state,'monopoly-game-lobby',input_limit=limits['input_limit'],output_limit=limits['output_limit'],max_cycles=limits['max_cycles'],max_added_units=limits['max_added_units'])
    policy={'format_version':1,'model':'deepseek/deepseek-v4.1-flash',
        'non_harness_authoring_effort':'none','explicit_effort_precedence':True}
    authority={'authority':'explicit user reply in active session',
        'question_item_id':'["request_user_input_async","call_d8bce353857b4a44a2d551c296fa9d3a",0]',
        'reply':'Activate the opt-in','run_id':'monopoly-game-lobby','config_sha256':config_hash,
        'policy':policy,'human_accepted':False,
        'application':'Atomic local transport setting, read once for each subsequent request; captured in-flight payloads and run journals are untouched'}
    # This is the operator-owned transport configuration, outside run journals.
    # Publish it atomically under its own guard. The executor keeps its run lease;
    # ModelCalls and each request's durable wire diagnostics retain prior payloads.
    with file_guard(state,'author-serialization-policy.guard'):
        target=state/'author-serialization-policy.json'
        proof_path=state/'model-authorizations/author-serialization-none-user-approved.json'
        if proof_path.exists():
            proof=json.loads(proof_path.read_bytes())
            if any(proof.get(k)!=v for k,v in authority.items()):raise ValueError('Existing approval differs')
        else:
            proof=authority|{'usage_at_publication':budget.totals(),
                'frozen_policy_test_sha256':sha256(Path(__file__).with_name('test_author_serialization_policy.py').read_bytes()).hexdigest()}
            atomic_write(state,proof_path.relative_to(state).as_posix(),json.dumps(proof,indent=2).encode())
        if target.exists() and json.loads(target.read_bytes())!=policy:raise ValueError('Preserve different existing policy')
        if not target.exists():atomic_write(state,'author-serialization-policy.json',json.dumps(policy,indent=2).encode())
        print(json.dumps({'activated':True,'model':config.coder.model,'scope':'unconfigured non-harness test authoring only',
            'explicit_effort_precedence':True,'config_unchanged':True,'run_journals_unchanged':True,
            'usage_observation':budget.totals(),'human_accepted':False}),flush=True)


if __name__=='__main__':main()
