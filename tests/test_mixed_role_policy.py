"""Current role policy and historical policy identity stay separate."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_all_coder_stages_and_judge_use_approved_low_policy():
    from mixed_backend_policy import role_profile
    p=role_profile()
    assert p['coder']=={'provider':'deepseek','model':'deepseek-flash','effort':'low'}
    assert p['judge']=={'provider':'codex','model':'gpt-6.1-sol','effort':'low'}
    assert p['optimizer']==p['coder']
    assert p['coder_stages']==['test_authoring','green','refactor','format_repair']
    assert p['limits']==[250000000,24000000,160,2]


def test_low_policy_receipt_needs_matching_grant_and_medium_history_is_preserved():
    from mixed_backend_policy import validate_judge_policy
    validate_judge_policy('medium','old',None)
    validate_judge_policy('low','new',{'judge_policy_sha256':'new','judge_effort':'low'})
    with pytest.raises(ValueError):validate_judge_policy('low','different',{'judge_policy_sha256':'new','judge_effort':'low'})
    with pytest.raises(ValueError):validate_judge_policy('low','new',None)
