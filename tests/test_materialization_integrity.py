"""Additional boundary checks discovered during materialization self-review."""

import os
import subprocess

import pytest

from test_candidate_materialization import candidate, setup_host
from unity_coder.adapters.unity.materialization import CandidateHost


def test_operational_roots_use_adapter_case_rules(setup_host):
    root, _, _ = setup_host
    with pytest.raises(ValueError):
        CandidateHost(root, "Assets/Game", assembly="game.runtime", dependencies={},
                      probe=lambda: {}, operational_roots=("assets",))


def test_mount_alias_cannot_hide_second_tree(setup_host):
    root, factory, _ = setup_host
    (root / "Assets/Game").rmdir()
    other = root / "Assets/Other"
    other.mkdir()
    link = root / "Assets/Game"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(other)], check=True, capture_output=True)
    else:
        link.symlink_to(other, target_is_directory=True)
    with pytest.raises(ValueError):
        factory().materialize("one", candidate())
    assert list(other.iterdir()) == []


def test_partial_install_never_becomes_ready_after_restart(setup_host, monkeypatch):
    root, factory, _ = setup_host
    from unity_coder.adapters.unity import materialization
    write = materialization.atomic_write
    def fail_game(destination, path, data):
        if destination == root / "Assets/Game":
            raise OSError("injected disk failure")
        return write(destination, path, data)
    monkeypatch.setattr(materialization, "atomic_write", fail_game)
    with pytest.raises(OSError):
        factory().materialize("one", candidate())
    with pytest.raises(ValueError, match="Interrupted"):
        factory().assert_ready("one")
