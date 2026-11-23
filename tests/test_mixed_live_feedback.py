"""Low-policy findings need an explicit grant and final-call provenance."""
from pathlib import Path
import sys
import pytest
from test_actual_judge_feedback import fixture as old_fixture

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_low_feedback_validates_the_new_policy_grant():
    from actual_judge_feedback import validate_finding
    request,effect,receipt,sdk,charge=old_fixture()
    receipt['identity']['effort']='low';receipt['identity']['backend_policy_sha256']='new-low'
    sdk['policy_sha256']='new-low'
    grant={'judge_effort':'low','judge_policy_sha256':'new-low'}
    assert 'ACTUAL independent' in validate_finding(request,effect,receipt,sdk,charge,'SHELL',grant=grant)
    with pytest.raises(ValueError):validate_finding(request,effect,receipt,sdk,charge,'SHELL')
