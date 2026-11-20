"""Freeze exact accounting of the new rejected judge call before recovery."""
import json
from pathlib import Path
from hashlib import sha256
import pytest
from operational_transport import retained_sol_key_limit_v51

CALL='v51-step4-prepare-review-TEST-SOCIAL'

def prepare(tmp_path):
    raw=(Path(__file__).parent/'evidence/sol-key-limit-v51.receipt.json').read_bytes()
    p=tmp_path/'.agent/runs/monopoly-game-lobby/model-calls'
    p.mkdir(parents=True)
    (p/(sha256(CALL.encode()).hexdigest()+'.json')).write_bytes(raw)
    return json.loads(raw),{'reserved':[512698,32768],'unit':'TEST-SOCIAL','version':51}

def test_full_unknown_reservation_is_retained(tmp_path):
    receipt,charge=prepare(tmp_path)
    assert retained_sol_key_limit_v51(tmp_path,CALL,receipt,charge)==(512698,32768)

@pytest.mark.parametrize('change',['settled','reduced','receipt','other_call'])
def test_changed_failure_or_accounting_is_rejected(tmp_path,change):
    receipt,charge=prepare(tmp_path);call=CALL
    if change=='settled':charge['actual']=[0,0]
    if change=='reduced':charge['reserved']=[0,0]
    if change=='receipt':receipt['failure']['http_status']=429
    if change=='other_call':call+='-retry'
    with pytest.raises((ValueError,FileNotFoundError)):
        retained_sol_key_limit_v51(tmp_path,call,receipt,charge)
