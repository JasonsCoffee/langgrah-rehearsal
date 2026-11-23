"""Bounded host-mediated context requests cannot become verdicts."""
from pathlib import Path
import sys
import pytest
from test_evidence_packet_manifest import packet

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_judge_can_request_exact_context_before_a_real_verdict():
    from judge_context_adapter import review
    calls=[];replies=[{'request_context':['optional']},{'defect_class':'implementation','explanation':'Source proves the defect.'}]
    def send(prompt,call):calls.append((prompt,call));return replies.pop(0)
    result=review(packet(),send,'op','defect',initial_input='initial')
    assert result['defect_class']=='implementation' and len(calls)==2
    assert 'obsolete example' in calls[-1][0] and calls[0][1]!=calls[1][1]


def test_unknown_context_and_incomplete_final_are_not_classifications():
    from judge_context_adapter import review
    from unity_coder.core.ai_models import ModelError
    with pytest.raises(ModelError):review(packet(),lambda *args:{'request_context':['not-existing']},'op','defect')


def test_repeated_context_requests_have_bounded_full_fallback():
    from judge_context_adapter import review
    from unity_coder.core.ai_models import ModelError
    calls=[]
    def send(*args):calls.append(True);return {'request_context':['optional']}
    with pytest.raises(ModelError):review(packet(),send,'op','defect')
    assert len(calls)==3
