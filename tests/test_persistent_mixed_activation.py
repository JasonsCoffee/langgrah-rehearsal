"""Applied routing persists across host restarts and rejects stale route overrides."""
from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_legacy_default_stays_but_qualified_active_route_survives_restart(tmp_path):
    from mixed_backend_policy import selected_backend,backend_record
    assert selected_backend(tmp_path,None)=='openrouter'
    assert selected_backend(tmp_path,'mixed')=='mixed'
    path=tmp_path/'model-authorizations/active-backend.json';path.parent.mkdir()
    path.write_text(json.dumps(backend_record()))
    assert selected_backend(tmp_path,None)=='mixed'
    with pytest.raises(ValueError):selected_backend(tmp_path,'codex')
    with pytest.raises(ValueError):selected_backend(tmp_path,'openrouter')


def test_changed_policy_cannot_be_loaded_as_the_active_route(tmp_path):
    from mixed_backend_policy import selected_backend,backend_record
    path=tmp_path/'model-authorizations/active-backend.json';path.parent.mkdir()
    path.write_text(json.dumps(backend_record()|{'profile_sha256':'different'}))
    with pytest.raises(ValueError):selected_backend(tmp_path,None)
