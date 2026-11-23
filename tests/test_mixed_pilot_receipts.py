"""A boolean pilot claim cannot activate changed model policies."""
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_pilot_boolean_without_real_matching_receipts_is_rejected(tmp_path):
    from mixed_backend_policy import validate_pilot_receipts,profile_sha256
    with pytest.raises(ValueError):validate_pilot_receipts(tmp_path,{}, {'roles_qualified':True,'profile_sha256':profile_sha256()})


def test_exact_model_effort_sdk_and_ledger_usage_are_required(tmp_path):
    from mixed_backend_policy import validate_pilot_receipts,profile_sha256,judge_policy
    calls={};roles={}
    for role,provider,model in [('coder','deepseek','deepseek-flash'),('judge','codex','gpt-6.1-sol')]:
        call='pilot-'+role;key=sha256(call.encode()).hexdigest();roles[role]=call
        identity={'call_id':call,'role':role,'model':model,'provider':provider,'effort':'low','backend_policy_sha256':judge_policy().sha256}
        reply={'model':model,'text':'{}','input_tokens':17,'output_tokens':7}
        path=tmp_path/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json');path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'identity':identity,'reply':reply}));calls[call]={'actual':[17,7]}
        if role=='judge':
            sdk=tmp_path/'codex-receipts'/(key+'.json');sdk.parent.mkdir();sdk.write_text(json.dumps({'text':'{}','input_tokens':17,'output_tokens':7,'policy_sha256':judge_policy().sha256}))
    qualified={'roles_qualified':True,'comparison_passed':True,'profile_sha256':profile_sha256(),'roles':roles}
    validate_pilot_receipts(tmp_path,calls,qualified)
    calls['pilot-judge']['actual']=[0,0]
    with pytest.raises(ValueError):validate_pilot_receipts(tmp_path,calls,qualified)
