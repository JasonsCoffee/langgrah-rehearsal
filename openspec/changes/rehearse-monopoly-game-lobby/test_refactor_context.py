"""Refactor prompts retain code/spec while final verification keeps full tests."""
from scoped_context import refactor_context


def test_refactor_omits_test_bodies_and_preserves_existing_source_provenance():
    files={'Runtime/Owned.cs':'code','Runtime/Ports.cs':'ports','Tests/Case.cs':'full tests',
           'spec.md':'requirements','sources/story.md':'large source',
           'read-only-test-excerpts.json':'original source hashes'}
    result=refactor_context(files,'spec.md')
    assert result['Runtime/Owned.cs']=='code' and result['Runtime/Ports.cs']=='ports'
    assert result['spec.md']=='requirements'
    assert result['read-only-test-excerpts.json']=='original source hashes'
    assert 'Tests/Case.cs' not in result and 'sources/story.md' not in result
    assert files['Tests/Case.cs']=='full tests'
