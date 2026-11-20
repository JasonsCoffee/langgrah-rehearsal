"""Frozen checks for fresh delegation after a proven unsent coder request."""
import pytest


def fixture():
    return ({'identity':{'call_id':'v27-step4-prepare-TEST-PARTY-TEST-PARTY','unit_id':'TEST-PARTY',
        'role':'coder','model':'deepseek/deepseek-v4.1-flash'},'failure':{
        'transport':'direct_preconnect','phase':'tls_establishment','failure_kind':'tls',
        'input_tokens':0,'output_tokens':0}},
        {'actual':[0,0],'reserved':[346651,65536],'unit':'TEST-PARTY','version':27})


def test_only_proven_unsent_coder_operation_is_eligible():
    from zero_http_recovery import zero_http_coder_unit
    record,charge=fixture()
    assert zero_http_coder_unit(record,charge,'v27-step4-prepare','deepseek/deepseek-v4.1-flash')=='TEST-PARTY'


@pytest.mark.parametrize('case',['role','post','unknown','paid','reply'])
def test_uncertain_or_changed_coder_effects_are_ineligible(case):
    from zero_http_recovery import zero_http_coder_unit
    record,charge=fixture()
    if case=='role':record['identity']['role']='judge'
    if case=='post':record['failure']['phase']='request'
    if case=='unknown':record['failure']={}
    if case=='paid':charge['actual']=[1,1]
    if case=='reply':record['reply']={'text':'{}'}
    with pytest.raises(ValueError):zero_http_coder_unit(record,charge,'v27-step4-prepare','deepseek/deepseek-v4.1-flash')
