"""Effort migration cannot refill the original Judge dispatch-count allowance."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import pytest
from unity_coder.core.ai_models import ModelError
from unity_coder.core.codex_backend import CodexPolicy

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_historical_claims_from_old_policy_still_consume_judge_bound(tmp_path):
    from mixed_backend_policy import RetainedJudgeClient
    state=tmp_path/'state';worker=tmp_path/'worker';state.mkdir();worker.mkdir()
    for number in range(2):
        call='old-'+str(number);key=sha256(call.encode()).hexdigest()
        receipt=state/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json');receipt.parent.mkdir(parents=True,exist_ok=True)
        receipt.write_text(json.dumps({'identity':{'call_id':call,'role':'judge','worker_backend':'codex_app_server','backend_policy_sha256':'old-medium'}}))
        claim=state/'codex-claims/old-medium'/(key+'.json');claim.parent.mkdir(parents=True,exist_ok=True);claim.write_text('{}')
    policy=CodexPolicy('judge','gpt-6.1-sol','low','dispatch_accounting','local-grant.json',2,65536)
    client=RetainedJudgeClient(policy,state,worker,exchange=lambda _:[],authorize=lambda _:True)
    with pytest.raises(ModelError):client.validate_output_limit(32768)


def test_profile_retains_original_framing_and_dispatch_bound():
    from mixed_backend_policy import role_profile
    assert role_profile()['framing_tokens']==65536 and role_profile()['max_calls_per_role']==200
