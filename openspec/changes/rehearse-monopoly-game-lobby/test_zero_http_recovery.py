"""Frozen classifier checks: unknown paid effects never enter automatic recovery."""
import copy
import pytest


def fixture():
    return ({'identity':{'call_id':'v26-step1-prepare-review-TEST-PRES-CORE',
        'unit_id':'TEST-PRES-CORE','role':'judge','model':'openai/gpt-6.1-sol'},
        'failure':{'transport':'direct_preconnect','phase':'tls_establishment',
        'failure_kind':'tls','input_tokens':0,'output_tokens':0}},
        {'actual':[0,0],'reserved':[297749,32768],'unit':'TEST-PRES-CORE','version':26})


def test_only_confirmed_zero_http_review_is_classified():
    from zero_http_recovery import zero_http_review_unit
    receipt,charge=fixture()
    assert zero_http_review_unit(receipt,charge,'v26-step1-prepare','openai/gpt-6.1-sol')=='TEST-PRES-CORE'


@pytest.mark.parametrize('mutation',['unknown','post','role','model','reply','operation','charge'])
def test_uncertain_paid_or_changed_identity_is_never_auto_resumed(mutation):
    from zero_http_recovery import zero_http_review_unit
    receipt,charge=fixture();receipt=copy.deepcopy(receipt)
    if mutation=='unknown':receipt['failure']={}
    if mutation=='post':receipt['failure']['phase']='request'
    if mutation=='role':receipt['identity']['role']='coder'
    if mutation=='model':receipt['identity']['model']='other'
    if mutation=='reply':receipt['reply']={'text':'{}'}
    if mutation=='operation':receipt['identity']['call_id']='v25-step1-prepare-review-TEST-PRES-CORE'
    if mutation=='charge':charge.pop('actual')
    with pytest.raises(ValueError):zero_http_review_unit(receipt,charge,'v26-step1-prepare','openai/gpt-6.1-sol')
