"""A real negative review needs new scope when all current test files are frozen."""
import importlib.util
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/frozen_review_rework.py')
    s=importlib.util.spec_from_file_location('frozen_review_rework',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def test_actual_negative_frozen_review_keeps_its_single_attempt():
    result=module().frozen_defect(('Tests/A.cs',),{'Tests/A.cs':'hash'},
        {'valid':False,'explanation':'Missing crossed-timestamp priority oracle'},1)
    assert result['attempts']==1 and 'crossed-timestamp' in result['reason']


@pytest.mark.parametrize('decision,owns',[
    ({'valid':True,'explanation':'ok'},('Tests/A.cs',)),
    ({'valid':False,'explanation':'gap'},('Tests/A.cs','Tests/New.cs')),
    ({'valid':False,'explanation':''},('Tests/A.cs',)),
])
def test_no_contract_route_for_approval_or_writable_scope(decision,owns):
    with pytest.raises(ValueError):module().frozen_defect(owns,{'Tests/A.cs':'hash'},decision,1)
