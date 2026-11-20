import importlib.util
from pathlib import Path
import pytest

def check():
    spec=importlib.util.spec_from_file_location('operational_transport',Path(__file__).with_name('operational_transport.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.retained_key_limit_failure

def fixture():
    return ({'identity':{'call_id':'v16-step1-prepare-review-TEST-APPEAR','role':'judge','unit_id':'TEST-APPEAR'},
        'failure':{'http_status':402,'limit_source':'openrouter_key_limit'}},
        {'version':16,'unit':'TEST-APPEAR','reserved':[440027,32768]})

def test_key_limit_keeps_full_unknown_charge():
    record,call=fixture()
    assert check()(record,call,16)==[440027,32768]
    assert 'actual' not in call

@pytest.mark.parametrize('change',['actual','version','unit','reservation','failure','role','reply'])
def test_key_limit_recovery_rejects_different_or_refunded_effect(change):
    record,call=fixture()
    if change=='actual':call['actual']=[0,0]
    if change=='version':call['version']=15
    if change=='unit':call['unit']='OTHER'
    if change=='reservation':call['reserved']=[True,32768]
    if change=='failure':record['failure']={'http_status':401}
    if change=='role':record['identity']['role']='coder'
    if change=='reply':record['reply']={'text':'not a failure'}
    with pytest.raises(ValueError):check()(record,call,16)
