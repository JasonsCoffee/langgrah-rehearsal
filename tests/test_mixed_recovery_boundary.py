"""Only the exact fully stopped current candidate can migrate policies."""
import copy
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def data():
    from mixed_backend_recovery import CANDIDATE,CONTRACT
    request={'request_id':'v70-step8-verify','candidate_revision':CANDIDATE,'contract_sha256':CONTRACT}
    return ({'run_id':'monopoly-game-lobby','outcome':'operational','contract_version':70,
        'candidate_revision':CANDIDATE,'contract_sha256':CONTRACT},
        {'request':request,'gate':'tests','status':'failed'},
        {'operation':'v70-step8-verify','stage':'verify','complete':True},
        {'identity':{'request':request,'unit':'ECON'}})


def test_exact_stop_accepts_only_a_new_policy_without_claiming_completion():
    from mixed_backend_recovery import validate_boundary
    validate_boundary(*data())


@pytest.mark.parametrize('bad',['candidate','outcome','transaction','pending','unit','contract'])
def test_changed_or_completed_effect_cannot_be_recovered(bad):
    from mixed_backend_recovery import validate_boundary
    result,evidence,transaction,pending=copy.deepcopy(data())
    if bad=='candidate':result['candidate_revision']='other'
    if bad=='outcome':result['outcome']='awaiting_human_review'
    if bad=='transaction':transaction['complete']=False
    if bad=='pending':pending['result']={'classification':'implementation','reason':'already complete'}
    if bad=='unit':pending['identity']['unit']='SHELL'
    if bad=='contract':result['contract_sha256']='other'
    with pytest.raises(ValueError):validate_boundary(result,evidence,transaction,pending)
