"""Cycle abandonment preserves candidates and never rewrites the user's tree."""
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from unity_coder.core.branches import CycleBranches


def setup(workspace, tmp_path):
    manager, repo, base, contract = workspace
    integration = manager.create_integration(1, base)
    path = contract.units[1].owns[0]
    (integration.path / path).write_bytes(b'candidate')
    git(integration.path, 'add', path)
    git(integration.path, 'commit', '-m', 'Candidate')
    candidate = git(integration.path, 'rev-parse', 'HEAD')
    return manager, repo, base, integration, candidate


def test_abandon_retains_cycle_tip_and_user_changes(workspace, tmp_path):
    manager, repo, base, integration, candidate = setup(workspace, tmp_path)
    (repo / 'user.txt').write_bytes(b'uncommitted user work')
    before = git(repo, 'status', '--porcelain')
    branches = CycleBranches(manager, tmp_path / 'state')
    result = branches.abandon(integration)
    assert result['candidate_revision'] == candidate
    assert result['restored_revision'] == base
    assert git(integration.path, 'rev-parse', 'HEAD') == base
    assert git(repo, 'rev-parse', integration.branch) == candidate
    assert git(repo, 'branch', '--show-current') == 'fixture/base'
    assert git(repo, 'status', '--porcelain') == before
    assert not git(repo, 'stash', 'list')
    assert CycleBranches(manager, tmp_path / 'state').abandon(integration) == result


def test_dirty_managed_worktree_is_not_discarded(workspace, tmp_path):
    manager, repo, base, integration, candidate = setup(workspace, tmp_path)
    (integration.path / 'unexpected.txt').write_bytes(b'inspect me')
    with pytest.raises(ValueError):
        CycleBranches(manager, tmp_path / 'state').abandon(integration)
    assert git(integration.path, 'rev-parse', 'HEAD') == candidate
    assert (integration.path / 'unexpected.txt').read_bytes() == b'inspect me'


def test_foreign_branch_is_not_switched(workspace, tmp_path):
    manager, repo, base, integration, candidate = setup(workspace, tmp_path)
    git(integration.path, 'switch', '-c', 'fixture/foreign')
    with pytest.raises(ValueError):
        CycleBranches(manager, tmp_path / 'state').abandon(integration)
    assert git(integration.path, 'branch', '--show-current') == 'fixture/foreign'


def test_interrupted_detach_reconciles_without_reapplying(workspace, tmp_path, monkeypatch):
    manager, repo, base, integration, candidate = setup(workspace, tmp_path)
    branches = CycleBranches(manager, tmp_path / 'state')
    original = branches._write
    def fail_completion(record):
        if record['state'] == 'complete':
            raise OSError('crash after Git detach')
        original(record)
    monkeypatch.setattr(branches, '_write', fail_completion)
    with pytest.raises(OSError): branches.abandon(integration)
    assert git(integration.path, 'rev-parse', 'HEAD') == base
    result = CycleBranches(manager, tmp_path / 'state').abandon(integration)
    assert result['state'] == 'complete'
    assert git(repo, 'rev-parse', integration.branch) == candidate


def test_changed_retained_tip_is_a_recovery_conflict(workspace, tmp_path):
    manager, repo, base, integration, candidate = setup(workspace, tmp_path)
    branches = CycleBranches(manager, tmp_path / 'state')
    branches.abandon(integration)
    git(repo, 'update-ref', 'refs/heads/' + integration.branch, base)
    with pytest.raises(ValueError): branches.abandon(integration)
