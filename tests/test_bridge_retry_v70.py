"""A fresh native retry needs proven compilation and zero test submission."""
from pathlib import Path
from copy import deepcopy
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def boundary():
    from mixed_backend_recovery import CONTRACT,CANDIDATE
    wire={'request_id':'v70-step9-verify','contract_version':70,'contract_sha256':CONTRACT,'candidate_revision':CANDIDATE}
    result={'outcome':'operational','reason':'Verification unavailable','contract_version':70,
        'contract_sha256':CONTRACT,'candidate_revision':CANDIDATE}
    evidence={'request':wire,'gate':'tests','status':'operational','test_result':None,
        'violations':[{'code':'operational','message':'No exact-project Bridge with FrameworkVerify tooling'}]}
    tx={'operation':'v70-step9-verify','stage':'verify','complete':True}
    compiled={'request':wire,'mode':'compile','status':'completed','passed':True,'violations':[]}
    return result,evidence,tx,compiled


def test_only_proven_pre_submission_boundary_is_resumable():
    from bridge_retry_v70 import validate_stop
    validate_stop(*boundary(),submitted=False)


@pytest.mark.parametrize('mutation',['submitted','candidate','request','incomplete','compile_failed','test_result'])
def test_ambiguous_or_different_boundary_blocks(mutation):
    from bridge_retry_v70 import validate_stop
    r,e,t,c=deepcopy(boundary());submitted=mutation=='submitted'
    if mutation=='candidate':r['candidate_revision']='other'
    if mutation=='request':e['request']['request_id']='other'
    if mutation=='incomplete':t['complete']=False
    if mutation=='compile_failed':c['passed']=False
    if mutation=='test_result':e['test_result']={'executed':['a']}
    with pytest.raises(ValueError):validate_stop(r,e,t,c,submitted=submitted)
