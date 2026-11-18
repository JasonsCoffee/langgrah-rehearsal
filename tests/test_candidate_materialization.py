"""Offline acceptance for a dedicated, single-mount verification host."""

import os
import subprocess

import pytest

from unity_coder.adapters.unity.materialization import CandidateHost


@pytest.fixture
def setup_host(tmp_path):
    host = tmp_path / "host"
    for directory in ("Assets/Game", "Packages", "ProjectSettings"):
        (host / directory).mkdir(parents=True)
    (host / "Packages/manifest.json").write_bytes(b"{}")
    (host / "Assets/shared.cs").write_bytes(b"shared")
    revisions = {"shared": "fixed"}
    def open_host():
        return CandidateHost(host, "Assets/Game", assembly="game.runtime",
                             dependencies={"shared": "fixed"}, probe=lambda: dict(revisions))
    return host, open_host, revisions


def candidate(**extra):
    return {"runtime.asmdef": b'{"name":"game.runtime"}',
            "runtime.asmdef.meta": b"guid: stable", "Code.cs": b"code", **extra}


def test_sync_preserves_metadata_and_removes_only_stale_managed_files(setup_host):
    root, factory, _ = setup_host
    worker = factory()
    worker.materialize("one", candidate(**{"Old.cs": b"old", "Old.cs.meta": b"guid: old"}))
    worker = factory()
    worker.materialize("two", candidate())
    assert not (root / "Assets/Game/Old.cs").exists()
    assert not (root / "Assets/Game/Old.cs.meta").exists()
    assert (root / "Assets/Game/runtime.asmdef.meta").read_bytes() == b"guid: stable"
    assert (root / "Assets/shared.cs").read_bytes() == b"shared"
    worker.assert_ready("two")


def test_unmanaged_content_is_never_adopted_or_removed(setup_host):
    root, factory, _ = setup_host
    (root / "Assets/Game/user.txt").write_bytes(b"user")
    with pytest.raises(ValueError, match="[Uu]nmanaged"):
        factory().materialize("one", candidate())
    assert (root / "Assets/Game/user.txt").read_bytes() == b"user"


@pytest.mark.parametrize("path", ["../shared.cs", ".git/config", "Code.cs/child", "code.cs"])
def test_invalid_candidates_fail_before_any_write(setup_host, path):
    root, factory, _ = setup_host
    with pytest.raises(ValueError):
        factory().materialize("one", candidate(**{path: b"bad"}))
    assert list((root / "Assets/Game").iterdir()) == []


def test_junction_escape_is_rejected(setup_host, tmp_path):
    root, factory, _ = setup_host
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "Assets/Game/escape"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        factory().materialize("one", candidate(**{"escape/bad.cs": b"bad"}))
    assert list(outside.iterdir()) == []


def test_nested_dependency_drift_is_rejected(setup_host):
    root, factory, revisions = setup_host
    worker = factory()
    revisions["shared"] = "changed"
    with pytest.raises(ValueError, match="[Dd]ependency"):
        worker.materialize("one", candidate())
    assert list((root / "Assets/Game").iterdir()) == []


def test_host_drift_is_persistently_detected(setup_host):
    root, factory, _ = setup_host
    factory().materialize("one", candidate())
    (root / "Assets/shared.cs").write_bytes(b"drift")
    with pytest.raises(ValueError, match="[Hh]ost drift"):
        factory().assert_ready("one")


def test_import_metadata_requires_new_reconciled_revision(setup_host):
    root, factory, _ = setup_host
    worker = factory()
    worker.materialize("one", candidate())
    (root / "Assets/Game/Code.cs.meta").write_bytes(b"guid: generated")
    assert worker.capture_import("one") == {"Code.cs.meta": b"guid: generated"}
    with pytest.raises(ValueError):
        factory().assert_ready("one")
    with pytest.raises(ValueError):
        factory().materialize("one", candidate(**{"Code.cs.meta": b"guid: generated"}))
    with pytest.raises(ValueError):
        factory().materialize("two", candidate())
    factory().materialize("two", candidate(**{"Code.cs.meta": b"guid: generated"}))
    factory().assert_ready("two")


@pytest.mark.parametrize("path", ["runtime.asmdef.meta", "Code.cs", "rogue.txt"])
def test_import_cannot_modify_existing_content_or_add_source(setup_host, path):
    root, factory, _ = setup_host
    worker = factory()
    worker.materialize("one", candidate())
    (root / "Assets/Game" / path).write_bytes(b"changed")
    with pytest.raises(ValueError):
        worker.capture_import("one")
    with pytest.raises(ValueError):
        worker.assert_ready("one")


def test_second_game_assembly_is_rejected(setup_host):
    root, factory, _ = setup_host
    (root / "Assets/other.asmdef").write_bytes(b'{"name":"game.runtime"}')
    with pytest.raises(ValueError, match="[Aa]ssembly"):
        factory().materialize("one", candidate())


def test_module_only_host_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="[Cc]omplete"):
        CandidateHost(tmp_path, "Assets/Game", assembly="game.runtime", dependencies={}, probe=lambda: {})


def test_candidate_identity_cannot_be_reused_for_different_bytes(setup_host):
    _, factory, _ = setup_host
    factory().materialize("one", candidate())
    changed = candidate()
    changed["Code.cs"] = b"new"
    with pytest.raises(ValueError):
        factory().materialize("one", changed)
