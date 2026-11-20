import importlib.util
from pathlib import Path
import pytest

def policy():
    path=Path(__file__).with_name('operational_transport.py')
    spec=importlib.util.spec_from_file_location('operational_transport',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.retained_transport_failure

def test_502_keeps_entire_uncertain_reservation():
    call={'reserved':[274267,32768],'version':8,'unit':'TEST-PRES-CORE'}
    record={'identity':{'role':'judge','call_id':'v8-step3-prepare-review-TEST-PRES-CORE','unit_id':'TEST-PRES-CORE'},'failure':{'http_status':502,'provider_name':'OpenAI'}}
    assert policy()(record,call,8)==[274267,32768]
    assert 'actual' not in call

@pytest.mark.parametrize('change',[{'actual':[0,0]},{'reserved':[0,32768]},{'version':7},{'unit':'SHELL'}])
def test_unknown_failure_must_retain_matching_positive_reservation(change):
    call={'reserved':[274267,32768],'version':8,'unit':'TEST-PRES-CORE'}|change
    record={'identity':{'role':'judge','call_id':'v8-step3-prepare-review-TEST-PRES-CORE','unit_id':'TEST-PRES-CORE'},'failure':{'http_status':502,'provider_name':'OpenAI'}}
    with pytest.raises(ValueError):policy()(record,call,8)

def test_different_failure_is_not_a_502_recovery():
    record={'identity':{'role':'judge','call_id':'v8-step3-prepare-review-TEST-PRES-CORE','unit_id':'TEST-PRES-CORE'},'failure':{'http_status':401}}
    with pytest.raises(ValueError):policy()(record,{'reserved':[100,100],'version':8,'unit':'TEST-PRES-CORE'},8)
