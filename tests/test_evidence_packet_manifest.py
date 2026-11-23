"""Immutable source identity and mandatory closure, without semantic rewriting."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def packet(extra=()):
    from evidence_packet import Source,make_packet
    return make_packet({'run':'run','contract':'c','candidate':'revision','unit':'U','stage':'judge','policy':'p'},
        (Source('code','Runtime/A.cs','class A { Helper h; }','patched',('helper',)),
         Source('helper','Runtime/H.cs','class Helper {}','dependency'),
         Source('optional','docs/history.md','obsolete example','optional'))+tuple(extra),
        ('code',),{'gate':'compile','failed':['T'],'violations':['CS0103']},{'Runtime/A.cs':'U'},('T',),'Keep behavior')


def test_required_closure_keeps_full_source_and_helper():
    from evidence_context_guard import mandatory_ids
    p=packet();assert mandatory_ids(p)=={'code','helper'}
    assert p.canonical_sha256==packet().canonical_sha256
    assert 'class A { Helper h; }' in p.canonical_input


def test_candidate_change_invalidates_packet_identity():
    from evidence_packet import make_packet
    p=packet();q=make_packet(p.identity|{'candidate':'other'},p.sources,p.required,p.mechanical,p.ownership,p.criteria,p.spec)
    assert q.canonical_sha256!=p.canonical_sha256


@pytest.mark.parametrize('kind',['dynamic','reflection','partial_unknown'])
def test_uncertain_dependency_promotes_all_admissible_source(kind):
    from evidence_packet import Source
    from evidence_context_guard import mandatory_ids
    p=packet((Source('uncertain','Runtime/X.cs','dynamic x;',kind),))
    assert mandatory_ids(p)=={s.id for s in p.sources}


def test_source_filter_rejects_coder_notes_secrets_and_private_reasoning():
    from evidence_packet import Source
    for kind in ['coder_notes','secret','reasoning','authorship']:
        with pytest.raises(ValueError):packet((Source('bad','private.txt','do not expose',kind),))


def test_duplicate_or_traversing_sources_are_rejected():
    from evidence_packet import Source
    with pytest.raises(ValueError):packet((Source('code','other.cs','x','optional'),))
    with pytest.raises(ValueError):packet((Source('bad','../secret','x','optional'),))
