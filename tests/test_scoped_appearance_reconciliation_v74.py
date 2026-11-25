"""Appearance authoring is limited to the two approved method bodies."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_appearance_scope_rejects_other_methods_and_prior_repairs(tmp_path):
    from approved_test_reconciliation_v74 import SCOPE, validate_patch
    unit = 'TEST-APPEAR'
    path = SCOPE[unit]['path']
    source = tmp_path / path
    source.parent.mkdir(parents=True)
    original = b'class Test { bool AssertVisibleThumbnail() { return false; } void Journey_ECON() { A(); } void Other() { B(); } }'
    source.write_bytes(original)
    proposed = original.replace(b'return false;', b'return true;').replace(b'A();', b'C();')
    validate_patch(unit, {path: proposed}, tmp_path)
    with pytest.raises(ValueError):
        validate_patch(unit, {path: proposed.replace(b'B();', b'D();')}, tmp_path)
    with pytest.raises(ValueError):
        validate_patch(unit, {path: proposed, 'Tests/LobbyChatMessageTests.cs': b''}, tmp_path)
