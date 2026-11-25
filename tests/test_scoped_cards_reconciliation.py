"""The Cards scope permits the four approved bodies and no unrelated edits."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_cards_author_cannot_edit_another_story(tmp_path):
    from approved_test_reconciliation_v83 import SCOPE, validate_patch

    unit = 'TEST-CARDS'
    relative = SCOPE[unit]['path']
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    before = b'''class T {
        string RoleAssociatedAmount() { return null; }
        bool IsMeasurableGraphicForCards() { return false; }
        bool IsRenderedLabelForCards() { return false; }
        void Story_L12_05() { Verify(); }
        void Story_L12_04() { Retain(); }
    }'''
    target.write_bytes(before)
    patch = before.replace(b'null', b'"200"').replace(b'false', b'true').replace(b'Verify();', b'Check();')
    validate_patch(unit, {relative: patch}, tmp_path)
    with pytest.raises(ValueError):
        validate_patch(unit, {relative: patch.replace(b'Retain();', b'Ignore();')}, tmp_path)
    with pytest.raises(ValueError):
        validate_patch(unit, {relative: patch, 'Tests/Unrelated.cs': b''}, tmp_path)
