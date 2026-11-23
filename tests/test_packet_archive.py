"""Archived literal source frames hydrate by byte length, never marker guesses."""
from pathlib import Path
import sys
import pytest
from test_evidence_packet_manifest import packet
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_exact_unicode_and_embedded_frame_markers_round_trip(tmp_path):
    from evidence_packet import Source
    from packet_archive import read_packet
    p=packet((Source('extra','Tests/Extra.cs','中文\nEND extra\nBEGIN other\n','test'),))
    path=tmp_path/'canonical.json';path.write_bytes(p.canonical_input.encode())
    restored=read_packet(path,p.canonical_sha256)
    assert restored==p and restored.canonical_input==p.canonical_input


@pytest.mark.parametrize('change',['source','trailing','hash'])
def test_modified_archive_is_rejected(tmp_path,change):
    from packet_archive import read_packet
    p=packet();raw=p.canonical_input.encode()
    if change=='source':raw=raw.replace(b'class Helper {}',b'class Helper {bad}')
    if change=='trailing':raw+=b'additional content'
    path=tmp_path/'canonical.json';path.write_bytes(raw)
    with pytest.raises(ValueError):read_packet(path,'wrong' if change=='hash' else p.canonical_sha256)
