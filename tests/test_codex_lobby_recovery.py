"""Freeze retention of a failed Codex call and production transport deadlines."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/codex_lobby.py')
    s=importlib.util.spec_from_file_location('codex_lobby_recovery',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def setup(tmp_path):
    call='v60-step6-prepare-TEST-CHAT-STATE-TEST-CHAT-STATE'
    identity={'call_id':call,'unit_id':'TEST-CHAT-STATE','role':'coder','provider':'codex',
        'model':'gpt-6.2-sol','worker_backend':'codex_app_server','backend_policy_sha256':'policy',
        'prompt_sha256':'prompt'}
    raw=json.dumps({'identity':identity,'failure':{}}).encode()
    folder=tmp_path/'.agent/runs/monopoly-game-lobby/model-calls';folder.mkdir(parents=True)
    (folder/(sha256(call.encode()).hexdigest()+'.json')).write_bytes(raw)
    claim={'operation_id':call,'policy_sha256':'policy','prompt_sha256':'prompt'}
    f=tmp_path/'codex-claims/policy';f.mkdir(parents=True)
    (f/(sha256(call.encode()).hexdigest()+'.json')).write_text(json.dumps(claim))
    charge={'unit':'TEST-CHAT-STATE','version':60,'reserved':[773062,65536]}
    proof={'receipt_sha256':sha256(raw).hexdigest(),'charge':charge.copy()}
    return call,charge,proof


def test_unknown_codex_effect_retains_exact_reservation(tmp_path):
    c,v,p=setup(tmp_path)
    assert module().retained_codex_call(tmp_path,c,v,p)==[773062,65536]


@pytest.mark.parametrize('bad',['settled','reduced','receipt','claim','different-call'])
def test_uncertain_call_cannot_be_refunded_or_reidentified(tmp_path,bad):
    c,v,p=setup(tmp_path)
    if bad=='settled':v['actual']=[0,0]
    elif bad=='reduced':v['reserved']=[0,0]
    elif bad=='receipt':p['receipt_sha256']='other'
    elif bad=='claim':
        (tmp_path/'codex-claims/policy'/(sha256(c.encode()).hexdigest()+'.json')).write_text('{}')
    else:c+='-other'
    with pytest.raises((ValueError,FileNotFoundError)):module().retained_codex_call(tmp_path,c,v,p)


def test_production_deadline_is_separate_from_the_two_call_pilot():
    assert module().PRODUCTION_TIMEOUT_SECONDS==180
