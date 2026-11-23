"""Architect unit instructions are mandatory evidence, never Coder commentary."""
from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_exact_unit_instructions_survive_canonical_and_optimized_review(tmp_path):
    from rehearsal_context_reviews import build_review_packet
    from evidence_context_guard import optimize,validate_delivery
    text='Inspect prefabs under an inactive parent.\r\nThe recording canvas must be active.\n'
    unit=SimpleNamespace(id='TEST-U',role='test',owns=('Tests/T.cs',),acceptance=('T',),instructions=text)
    workers=SimpleNamespace(root=tmp_path,contract=SimpleNamespace(sha256='c',spec=SimpleNamespace(path='specs/spec.md'),units=(unit,)),
        services=SimpleNamespace(state={'patches':{}}))
    packet=build_review_packet(workers,unit,{'Tests/T.cs':'void T() {}','specs/spec.md':'Actual behavior'},
        {'gate':'source','unit_instructions':'untrusted replacement'},'policy','test_review')
    assert packet.mechanical['unit_instructions']==text
    result=optimize(packet,{'canonical_sha256':packet.canonical_sha256,'selected':[]},min_reduction=0)
    validate_delivery(packet,result)
    assert 'inactive parent' in result.optimized_input
    assert 'untrusted replacement' not in result.optimized_input
