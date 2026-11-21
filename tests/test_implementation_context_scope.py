"""Role context stays complete for ownership while avoiding unrelated bodies."""
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/implementation_context_scope.py')
    s=importlib.util.spec_from_file_location('implementation_context_scope',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


@pytest.mark.parametrize('unit,suite',[('SHELL','LobbyPresentationCoreTests'),('ECON','LobbyEconomyTests'),('MATCH','LobbyMatchTests'),('SOCIAL','LobbySocialTests'),('RECORDS','LobbyRecordsSettingsTests')])
def test_full_owned_suite_harness_spec_and_runtime_are_unchanged(unit,suite):
    own='Tests/'+suite+'.cs';other='Tests/UnrelatedTests.cs'
    files={own:'exact full tests',other:'unrelated full tests','Tests/LobbyHarness.cs':'all shared helpers',
           'spec.md':'complete specification','Runtime/Owned.cs':'complete implementation'}
    before=dict(files);v=module().scoped(unit,files)
    assert all(v[p]==files[p] for p in (own,'Tests/LobbyHarness.cs','spec.md','Runtime/Owned.cs'))
    assert other not in v and files==before
    assert other in json.loads(v['readonly-context-scope/provenance.json'])['omitted_provided_text_sha256']


def test_unknown_scope_cannot_silently_omit_source():
    with pytest.raises(ValueError):module().scoped('UNKNOWN',{'Tests/T.cs':'source'})
