"""Compact read-only evidence without dropping current acceptance clauses."""
from compact_context import compact_author_context


def test_compaction_preserves_current_code_clauses_and_adapter_implementation():
    files={'Tests/Current.cs':'owned body','Tests/Legacy.acceptance.md':'historical claim',
           'spec/acceptance-conditions.v2.json':'original source clauses',
           'spec/selected-original-stories.md':'duplicate original source clauses',
           'spec/proposal.md':'whole proposal', 'Runtime/Ports.cs':'public API',
           'Tests/LobbyHarness.cs':'namespace Tests { class Adapter { void Observe(){} } class LobbyHarnessTests { void Unrelated(){} } }'}
    output=compact_author_context('TEST-PRES-CORE',('Tests/Current.cs','Tests/Current.acceptance.md'),files)
    assert output['Tests/Current.cs']=='owned body'
    assert output['spec/acceptance-conditions.v2.json']=='original source clauses'
    assert output['Runtime/Ports.cs']=='public API'
    assert 'Observe()' in output['Tests/LobbyHarness.cs']
    assert 'Unrelated()' not in output['Tests/LobbyHarness.cs']
    assert 'Tests/Legacy.acceptance.md' not in output
    assert 'spec/selected-original-stories.md' not in output
    assert files['Tests/Legacy.acceptance.md']=='historical claim'
