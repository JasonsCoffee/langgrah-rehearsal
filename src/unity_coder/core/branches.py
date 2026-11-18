"""Durable coordinator-owned cycle branch transitions."""
import json
from pathlib import Path
from typing import TypedDict, Literal, cast
from .journal import run_prefix
from .ownership import confined_path
from .storage import atomic_write, file_guard
from .workspaces import Workspace, WorkspaceManager, git


class AbandonRecord(TypedDict):
    branch: str
    workspace: str
    candidate_revision: str
    restored_revision: str
    contract_sha256: str
    state: Literal['pending', 'complete']


class CycleBranches:
    def __init__(self, manager: WorkspaceManager, state_root: Path) -> None:
        self.manager = manager
        self.root = state_root.resolve()
        if self.root.is_relative_to(manager.repository) or self.root.is_relative_to(manager.workspace_root):
            raise ValueError('Branch journal must be outside managed and user worktrees')
        prefix = run_prefix(manager.run_id)
        self.path = prefix + f'/abandon-v{manager.contract.contract_version}.json'
        self.guard = prefix + '/branches.guard'

    def _write(self, record: AbandonRecord) -> None:
        atomic_write(self.root, self.path, json.dumps(record, sort_keys=True).encode())

    def abandon(self, integration: Workspace) -> AbandonRecord:
        """Detach only the registered clean integration tree; retain its cycle ref.

        An interrupted detach is reconciled using durable intent. Dirty or foreign
        state is left untouched, never stashed, cleaned or reset to make it fit.
        """
        manager = self.manager
        expected_branch = f'agent/{manager.run_id}/cycle-{manager.contract.contract_version}'
        if (manager._handles.get(integration.path) != integration or integration.kind != 'integration'
            or integration.branch != expected_branch):
            raise ValueError('Abandon requires a registered cycle integration workspace')
        with file_guard(self.root, self.guard):
            branch = git(integration.path, 'branch', '--show-current').decode().strip()
            head = git(integration.path, 'rev-parse', 'HEAD').decode().strip()
            tip = git(manager.repository, 'rev-parse', 'refs/heads/' + expected_branch).decode().strip()
            if git(integration.path, 'status', '--porcelain', '--untracked-files=all'):
                raise ValueError('Dirty integration requires reconciliation before abandonment')
            path = confined_path(self.root, self.path)
            identity = dict(branch=expected_branch,
                workspace=integration.path.relative_to(manager.workspace_root).as_posix(),
                restored_revision=integration.base_revision, contract_sha256=manager.contract.sha256)
            if path.exists():
                record = cast(AbandonRecord, json.loads(path.read_bytes()))
                if any(record.get(k) != v for k, v in identity.items()) or record['candidate_revision'] != tip:
                    raise ValueError('Abandon intent or retained candidate changed')
            else:
                manager._assert_handle(integration, 'integration')
                if head != tip:
                    raise ValueError('Cycle tip differs from integration HEAD')
                record = cast(AbandonRecord, dict(identity, candidate_revision=tip, state='pending'))
                self._write(record)
            if branch == '' and head == integration.base_revision:
                # Git detach completed, including after a crash before the write.
                if record['state'] != 'complete':
                    record['state'] = 'complete'
                    self._write(record)
                return record
            if branch != expected_branch or head != record['candidate_revision'] or record['state'] != 'pending':
                raise ValueError('Managed Git state conflicts with abandonment intent')
            git(integration.path, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                'switch', '--detach', integration.base_revision)
            record['state'] = 'complete'
            self._write(record)
            return record
