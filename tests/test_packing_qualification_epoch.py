"""A changed packing format cannot activate against a previous-format pilot."""
from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_current_format_requires_a_distinct_qualification_record(tmp_path):
    from mixed_backend_policy import active_qualification,QUALIFICATION_REF
    assert QUALIFICATION_REF!='context-optimization/pilot-qualified.json'
    old=tmp_path/'context-optimization/pilot-qualified.json';old.parent.mkdir()
    old.write_text(json.dumps({'packing_format_version':1,'roles_qualified':True}))
    with pytest.raises((ValueError,FileNotFoundError)):active_qualification(tmp_path,{})


def test_previous_format_cannot_masquerade_as_current(tmp_path):
    from mixed_backend_policy import active_qualification,QUALIFICATION_REF
    p=tmp_path/QUALIFICATION_REF;p.parent.mkdir()
    p.write_text(json.dumps({'packing_format_version':1,'roles_qualified':True}))
    with pytest.raises(ValueError):active_qualification(tmp_path,{})


def test_pilot_call_namespace_changes_without_resetting_envelope():
    from mixed_backend_pilot import PILOT_PREFIX,PACKING_VERSION
    assert PACKING_VERSION==2 and PILOT_PREFIX=='v70-migration-packed-v2'
