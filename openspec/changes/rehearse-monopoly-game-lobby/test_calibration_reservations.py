"""Frozen checks for non-mutating calibration reservations retained at recovery."""
from hashlib import sha256
import json
import pytest
import operational_transport


@pytest.mark.parametrize('change',[None,'receipt','actual','role','unknown_call'])
def test_only_exact_operator_recorded_probe_reservations_are_reconciled(tmp_path,change):
    call='judge-switch-v23-glm-json-review'
    receipt={'identity':{'call_id':call,'role':'judge','unit_id':'TEST-VIP','model':'z-ai/glm-5.3-flash','output_limit':32768},'failure':{}}
    if change=='role':receipt['identity']['role']='coder'
    reserved={'reserved':[1200,32768]}
    if change=='actual':reserved['actual']=[0,0]
    raw=json.dumps(receipt).encode();folder=tmp_path/'.agent/runs/monopoly-game-lobby/model-calls';folder.mkdir(parents=True)
    (folder/(sha256(call.encode()).hexdigest()+'.json')).write_bytes(raw)
    manifest={'non_mutating_calibration':True,'usage_unknown_retained':True,'calls':{call:{'receipt_sha256':sha256(raw).hexdigest(),'reservation':reserved}}}
    auth=tmp_path/'model-authorizations';auth.mkdir();(auth/'glm-json-probe-reservations-v23.json').write_text(json.dumps(manifest))
    if change=='receipt':(folder/(sha256(call.encode()).hexdigest()+'.json')).write_bytes(raw+b' ')
    if change=='unknown_call':call='unrelated-paid-call'
    invoke=lambda:operational_transport.retained_calibration_failure(tmp_path,call,receipt,reserved)
    if change is None:assert invoke()==(1200,32768)
    else:
        with pytest.raises(ValueError):invoke()
