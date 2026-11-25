"""Retain all three explicit authoring scopes through a budget recovery."""
from importlib import import_module
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


@pytest.mark.parametrize('module', ['approved_test_reconciliation_v75','approved_test_reconciliation_v76'])
def test_nfr_guard_preserves_every_unapproved_method(tmp_path, module):
    guard = import_module(module)
    unit = 'TEST-PRES-NFR'
    relative = guard.SCOPE[unit]['path']
    target = tmp_path/relative
    target.parent.mkdir(parents=True)
    original = b'class T { void Story_NFR_01(){ A(); } void Story_NFR_02(){ A(); } void Story_NFR_03(){ A(); } void Story_NFR_04(){ A(); } void Other(){ B(); } }'
    target.write_bytes(original)
    patch = original.replace(b'A();', b'try { A(); } finally { Cleanup(); }')
    guard.validate_patch(unit,{relative:patch},tmp_path)
    with pytest.raises(ValueError):
        guard.validate_patch(unit,{relative:patch.replace(b'B();',b'C();')},tmp_path)
    with pytest.raises(ValueError):
        guard.validate_patch(unit,{relative:patch,guard.SCOPE['TEST-APPEAR']['path']:b''},tmp_path)
