"""Frozen workspace tests use only disposable nested Git repositories."""

import subprocess

import pytest

from test_contracts import bundle, load, Rules
from unity_coder.core.workspaces import WorkspaceManager
from unity_coder.core.execution_host import ExecutionHost


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def workspace(bundle, tmp_path):
    contract = load(bundle)
    repo = bundle[1] / "host/Assets/Game"
    repo.mkdir(parents=True)
    host = bundle[1] / "host"
    git(host, "init", "-b", "fixture/host")
    git(host, "config", "user.name", "Offline Fixture")
    git(host, "config", "user.email", "fixture@example.invalid")
    (host / "shared.txt").write_bytes(b"read-only host")
    git(host, "add", "shared.txt")
    git(host, "commit", "-m", "Host fixture")
    git(repo, "init", "-b", "fixture/base")
    git(repo, "config", "user.name", "Offline Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    for unit in contract.units:
        for path in unit.owns:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"baseline")
    for ref in (contract.spec, contract.presentation_ref, contract.coding_profile_ref, contract.environment_ref):
        target = repo / ref.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((bundle[1] / ref.path).read_bytes())
    git(repo, "add", ".")
    git(repo, "commit", "-m", "Fixture baseline")
    base = git(repo, "rev-parse", "HEAD")
    manager = WorkspaceManager(repo, tmp_path / "external", contract, Rules(),
                               run_id="run1", imported_roots=(repo.parent,))
    return manager, repo, base, contract


def test_units_are_external_isolated_module_worktrees(workspace):
    manager, repo, base, _ = workspace
    first = manager.create_unit("U1-state", base, {})
    second = manager.create_unit("U2-system", base, {"U1-state": base})
    assert not first.path.is_relative_to(repo.parent)
    assert first.path != second.path and first.base_revision == base
    assert not (first.path / "Assets").exists()
    assert (first.path / ".git").is_file()
    assert git(repo, "branch", "--show-current") == "fixture/base"


def test_worktree_under_import_tree_rejected_before_creation(workspace):
    _, repo, _, contract = workspace
    with pytest.raises(ValueError):
        WorkspaceManager(repo, repo.parent / "unsafe", contract, Rules(), run_id="bad", imported_roots=(repo.parent,))
    assert not (repo.parent / "unsafe").exists()


def test_capture_rejects_foreign_changes(workspace):
    manager, _, base, _ = workspace
    handle = manager.create_unit("U1-state", base, {})
    (handle.path / "Runtime/Script/Queue/QueueSystem.cs").write_bytes(b"foreign")
    with pytest.raises(ValueError): manager.capture(handle)


def test_capture_tracks_owned_deletion_and_revision(workspace):
    manager, _, base, _ = workspace
    handle = manager.create_unit("U1-state", base, {})
    (handle.path / "Runtime/Script/Queue/DinerState.cs").unlink()
    candidate = manager.capture(handle)
    assert candidate.changes == {"Runtime/Script/Queue/DinerState.cs": None}
    assert candidate.base_revision == base and candidate.unit_id == "U1-state"


def test_only_coordinator_integrates_and_preserves_starting_user_work(workspace):
    manager, repo, base, _ = workspace
    own = "Runtime/Script/Queue/DinerState.cs"
    (repo / own).write_bytes(b"user uncommitted work")
    handle = manager.create_unit("U1-state", base, {})
    (handle.path / own).write_bytes(b"candidate")
    candidate = manager.capture(handle)
    integration = manager.create_integration(1, base)
    revision = manager.integrate(integration, candidate, {})
    assert revision != base and (integration.path / own).read_bytes() == b"candidate"
    assert (repo / own).read_bytes() == b"user uncommitted work"
    assert git(repo, "rev-parse", "HEAD") == base
    assert git(integration.path, "branch", "--show-current") == "agent/run1/cycle-1"
    with pytest.raises(ValueError): manager.integrate(handle, candidate, {})


def test_stale_dependency_candidate_rejected(workspace):
    manager, _, base, _ = workspace
    handle = manager.create_unit("U2-system", base, {"U1-state": "old"})
    (handle.path / "Runtime/Script/Queue/QueueSystem.cs").write_bytes(b"candidate")
    candidate = manager.capture(handle)
    integration = manager.create_integration(1, base)
    with pytest.raises(ValueError): manager.integrate(integration, candidate, {"U1-state": "new"})
    assert git(integration.path, "rev-parse", "HEAD") == base


@pytest.mark.parametrize("path", ["../other/file", ".git", ".git/config", "Runtime/Script/Queue/QueueSystem.cs", "Tests/Runtime/Script/QueueReorderTests.cs"])
def test_execution_host_denies_unowned_or_metadata_writes(workspace, path):
    manager, _, base, contract = workspace
    handle = manager.create_unit("U1-state", base, {})
    host = ExecutionHost(handle, contract, Rules())
    with pytest.raises(ValueError): host.write_file(path, b"forbidden")


def test_execution_host_allows_owned_write_but_no_arbitrary_shell(workspace):
    manager, _, base, contract = workspace
    handle = manager.create_unit("U1-state", base, {})
    host = ExecutionHost(handle, contract, Rules())
    path = "Runtime/Script/Queue/DinerState.cs"
    host.write_file(path, b"allowed")
    assert host.read_file(path) == b"allowed"
    with pytest.raises(ValueError): host.run_command(["git", "push"])
    with pytest.raises(ValueError): host.read_file(".git")


def test_unsupported_agent_execution_mode_fails_preflight(workspace):
    manager, _, base, contract = workspace
    handle = manager.create_unit("U1-state", base, {})
    with pytest.raises(ValueError): ExecutionHost(handle, contract, Rules(), mode="unrestricted-shell")
