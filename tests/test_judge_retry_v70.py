"""Unknown paid Judge usage remains reserved before fresh native continuation."""
import copy
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/judge_retry_v70.py')
    spec=importlib.util.spec_from_file_location('judge_retry_v70',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def fixture():
    m=module();result={'outcome':'operational','reason':'Model transport requires reconciliation',
        'contract_version':70,'contract_sha256':m.CONTRACT,'candidate_revision':m.CANDIDATE}
    evidence={'gate':'compile','status':'failed','related_units':['ECON'],'request':{'request_id':'v70-step5-verify',
        'contract_sha256':m.CONTRACT,'candidate_revision':m.CANDIDATE}}
    pending={'identity':{'request':evidence['request'],'unit':'ECON'}}
    charge={'reserved':[934582,32768],'unit':'ECON','version':70}
    return m,result,evidence,pending,charge


def test_only_exact_unresolved_paid_judge_stop_can_resume_without_refund():
    m,result,evidence,pending,charge=fixture()
    m.validate_stop(result,evidence,pending,charge,sdk_exists=False)


@pytest.mark.parametrize('bad',['candidate','gate','completed_effect','refund','sdk'])
def test_mismatched_or_already_completed_effect_is_rejected(bad):
    m,result,evidence,pending,charge=fixture();sdk=False
    if bad=='candidate':result['candidate_revision']='different'
    if bad=='gate':evidence['gate']='tests'
    if bad=='completed_effect':pending['result']={'classification':'implementation','reason':'untrusted'}
    if bad=='refund':charge['actual']=[0,0]
    if bad=='sdk':sdk=True
    with pytest.raises(ValueError):m.validate_stop(result,evidence,pending,charge,sdk_exists=sdk)
