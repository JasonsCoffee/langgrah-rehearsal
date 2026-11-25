"""Protect the approved VIP scope across consecutive contracts."""
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


@pytest.mark.parametrize('version',[79,82])
def test_vip_author_cannot_change_the_story_or_an_unrelated_test(tmp_path,version):
    guard=import_module(f'approved_test_reconciliation_v{version}')
    unit = 'TEST-VIP'
    relative = guard.SCOPE[unit]['path']
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    before = b'''class T {
        void AssertRulesRowsForLevels() { OldRow(); }
        bool ContainsDistinctAmountField() { return false; }
        void Story_L12_08() { Verify(); }
    }'''
    target.write_bytes(before)
    patch = before.replace(b'OldRow();', b'NewRow();').replace(b'false', b'true')
    guard.validate_patch(unit, {relative: patch}, tmp_path)
    with pytest.raises(ValueError):
        guard.validate_patch(unit, {relative: patch.replace(b'Verify();', b'Ignore();')}, tmp_path)
    with pytest.raises(ValueError):
        guard.validate_patch(unit, {relative: patch, 'Tests/Unrelated.cs': b''}, tmp_path)
