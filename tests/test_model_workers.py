import json
import pytest
from unity_coder.core.model_workers import parse_patch, parse_judgement


def test_patch_contains_only_owned_full_text():
    patch,reason=parse_patch(json.dumps({'files':{'src/a.txt':'new contents'},'reason':'implementation'}),('src/a.txt',))
    assert patch=={'src/a.txt':b'new contents'} and reason=='implementation'


@pytest.mark.parametrize('files',[{'tests/a.txt':'overwrite'}, {'../a.txt':'escape'}, {'src/a.txt':None}])
def test_invalid_model_patch_is_rejected(files):
    with pytest.raises(ValueError): parse_patch(json.dumps({'files':files,'reason':'change'}),('src/a.txt',))


def test_no_change_refactor_requires_reason():
    assert parse_patch('{"files":{},"reason":"Already minimal"}',('src/a.txt',))==({},'Already minimal')
    with pytest.raises(ValueError): parse_patch('{"files":{},"reason":""}',('src/a.txt',))


def test_judge_is_defect_router_not_acceptance_authority():
    assert parse_judgement('{"defect_class":"implementation","explanation":"Missing branch"}')==('implementation','Missing branch')
    with pytest.raises(ValueError): parse_judgement('{"defect_class":"pass","explanation":"Looks good"}')
