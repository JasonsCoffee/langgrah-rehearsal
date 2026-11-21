"""Coder repair guidance must be the actual independent Judge's matching finding."""
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/actual_judge_feedback.py')
    s=importlib.util.spec_from_file_location('actual_judge_feedback',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fixture():
    request={'request_id':'v68-step9-verify','candidate_revision':'candidate'}
    text=json.dumps({'defect_class':'implementation','explanation':'Logical equivalence does not satisfy the active analyzer syntax.'})
    effect={'identity':{'request':request,'unit':'SHELL'},'result':{'classification':'implementation','reason':json.loads(text)['explanation']}}
    receipt={'identity':{'model':'gpt-6.1-sol','effort':'medium','role':'judge','backend_policy_sha256':'policy'},'reply':{'text':text,'model':'gpt-6.1-sol'}}
    sdk={'text':text,'policy_sha256':'policy','input_tokens':123,'output_tokens':45}
    return request,effect,receipt,sdk,{'actual':[123,45]}


def test_exact_judge_rationale_is_delivered_to_the_owning_coder():
    args=fixture();note=module().validate_finding(*args,'SHELL')
    assert 'Logical equivalence' in note and 'independent Judge' in note


@pytest.mark.parametrize('bad',['request','reason','model','usage'])
def test_stale_or_unproven_findings_are_rejected(bad):
    request,effect,receipt,sdk,charge=fixture()
    if bad=='request':request=request|{'candidate_revision':'other'}
    if bad=='reason':effect['result']['reason']='invented'
    if bad=='model':receipt['identity']['model']='other'
    if bad=='usage':charge['actual'][0]=0
    with pytest.raises(ValueError):module().validate_finding(request,effect,receipt,sdk,charge,'SHELL')
