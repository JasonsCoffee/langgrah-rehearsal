"""Chat approval preserves all enabled test cases and peer-owned methods."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_only_two_helpers_can_change_without_touching_enabled_tests(tmp_path):
    from approved_test_reconciliation_v73 import CHAT,validate_patch
    path=CHAT['path'];p=tmp_path/path;p.parent.mkdir(parents=True)
    raw=b'class T { void MsgAvatarSpritesForRow() { A(); } void MsgPermittedRowGraphics() { B(); } [Test] void Story_L13_12() { Assert(); } }'
    p.write_bytes(raw)
    fixed=raw.replace(b'A();',b'LookupMessage();').replace(b'B();',b'CheckAvatarBinding();')
    validate_patch('TEST-CHAT-MSG',{path:fixed},tmp_path)
    for bad in [fixed.replace(b'[Test]',b'[Ignore]'),fixed.replace(b'Assert();',b'Skip();'),fixed.replace(b'class T',b'class Other')]:
        with pytest.raises(ValueError):validate_patch('TEST-CHAT-MSG',{path:bad},tmp_path)


def test_original_two_scopes_keep_original_owned_note_paths():
    from approved_test_reconciliation_v73 import author_paths
    from approved_test_reconciliation_v71 import author_paths as previous
    for unit in ('TEST-PRES-CORE','TEST-PRES-NFR'):
        assert author_paths(unit)==previous(unit)
