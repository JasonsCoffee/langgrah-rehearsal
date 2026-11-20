"""A replacement call preserves the exact rejected paid call and all history."""
from hashlib import sha256
import json
from pathlib import Path
import pytest
from test_lobby_context_recovery import module


def fixture(state):
    call='v66-step8-verify-judge-SHELL';key=sha256(call.encode()).hexdigest()
    identity={'call_id':call,'unit_id':'SHELL','worker_backend':'codex_app_server','provider':'codex',
              'backend_policy_sha256':'policy','prompt_sha256':'prompt'}
    raw=json.dumps({'identity':identity,'failure':{}}).encode()
    p=state/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json');p.parent.mkdir(parents=True);p.write_bytes(raw)
    p=state/'codex-claims/policy'/(key+'.json');p.parent.mkdir(parents=True);p.write_text(json.dumps({'operation_id':call,'policy_sha256':'policy','prompt_sha256':'prompt'}))
    p=state/'model-authorizations/codex-retained-calls.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'authority':'existing','provenance':'original','calls':{'old':{'unchanged':True}}}))
    return call,{'reserved':[12345,32768],'unit':'SHELL','version':66},sha256(raw).hexdigest(),p


def test_failed_call_is_appended_without_resetting_old_proof_or_charge(tmp_path):
    call,charge,digest,path=fixture(tmp_path);before=json.loads(json.dumps(charge))
    module().register_retained_call(tmp_path,call,charge,digest)
    result=json.loads(path.read_bytes())
    assert result['calls']['old']=={'unchanged':True} and result['authority']=='existing'
    assert result['calls'][call]=={'receipt_sha256':digest,'charge':before} and charge==before


def test_changed_failure_receipt_cannot_be_registered(tmp_path):
    call,charge,digest,path=fixture(tmp_path);before=path.read_bytes()
    with pytest.raises(ValueError):module().register_retained_call(tmp_path,call,charge,'wrong')
    assert path.read_bytes()==before
