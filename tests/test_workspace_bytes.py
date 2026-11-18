"""Worktree checkout must preserve frozen committed bytes on every platform."""
from test_workspaces import workspace, git
from test_contracts import bundle


def test_checkout_ignores_machine_line_ending_conversion(workspace):
    manager, repo, base, contract = workspace
    path = contract.units[0].owns[0]
    expected = b'first line\nsecond line\n'
    (repo / path).write_bytes(expected)
    git(repo, 'add', path)
    git(repo, 'commit', '-m', 'Freeze LF fixture')
    base = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'config', 'core.autocrlf', 'true')
    unit = manager.create_unit('U1-state', base, {})
    integration = manager.create_integration(1, base)
    assert (unit.path / path).read_bytes() == expected
    assert (integration.path / path).read_bytes() == expected
    assert git(repo, 'config', 'core.autocrlf') == 'true'
