"""Metadata-only completion after authenticated exact-candidate review."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from .constraints import LearnedConstraint, accepted_constraints
from .ownership import confined_path
from .review import ReviewGate
from .storage import atomic_write, file_guard
from .verification import VerificationRequest
from .workspaces import Workspace, WorkspaceManager, git


class CandidateCompletion:
    def __init__(self, manager: WorkspaceManager, integration: Workspace, review: ReviewGate) -> None:
        self.manager, self.integration, self.review = manager, integration, review
        self.path = review.lifecycle.prefix + f'/completion-v{manager.contract.contract_version}.json'
        self.guard = review.lifecycle.prefix + '/completion.guard'
        if review.root.resolve().is_relative_to(integration.path):
            raise ValueError('Completion journal must be outside integration worktree')

    def _publish(self, before: str, after: str) -> None:
        git(self.integration.path, 'update-ref', 'refs/heads/' + self.integration.branch, after, before)

    def _files(self, revision: str) -> dict[str, bytes]:
        paths = git(self.integration.path, 'ls-tree', '-r', '--name-only', '-z', revision).decode().split('\0')
        return {p: git(self.integration.path, 'show', revision + ':' + p) for p in paths if p}

    def _build(self, before: str, content: bytes, changed: bool) -> str:
        # A separate index avoids staging anything in a user or coding workspace.
        with TemporaryDirectory(prefix='framework-completion-') as temporary:
            environment = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
            def command(*args: str, data: bytes | None = None) -> str:
                result = subprocess.run(['git', '-C', str(self.integration.path), *args],
                    input=data, capture_output=True, env=environment, check=False)
                if result.returncode:
                    raise ValueError('Completion Git operation failed: ' + result.stderr.decode(errors='replace'))
                return result.stdout.decode().strip()
            command('read-tree', before)
            if changed:
                prior = command('ls-tree', before, '--', 'AGENTS.md')
                mode = prior.split()[0] if prior else '100644'
                if mode not in ('100644', '100755'):
                    raise ValueError('Managed constraints must be a regular file')
                blob = command('hash-object', '-w', '--stdin', data=content)
                command('update-index', '--add', '--cacheinfo', mode, blob, 'AGENTS.md')
            tree = command('write-tree')
            return command('commit-tree', tree, '-p', before, '-m', 'Record accepted constraint provenance')

    def complete(self, request: VerificationRequest,
                 entries: tuple[LearnedConstraint, ...]) -> dict[str, object]:
        manager, workspace, review = self.manager, self.integration, self.review
        with file_guard(review.root, self.guard):
            manager._assert_handle(workspace, 'integration')
            if (workspace.branch != f'agent/{manager.run_id}/cycle-{manager.contract.contract_version}'
                or request.run_id != manager.run_id or request.contract_sha256 != manager.contract.sha256
                or request.contract_version != manager.contract.contract_version):
                raise ValueError('Completion identity differs from managed cycle')
            approval = review.state()
            wire = json.loads(json.dumps(asdict(request)))
            if approval.get('request') != wire or approval.get('decision') != 'accept':
                raise ValueError('Exact-candidate human approval required')
            before = request.candidate_revision
            files = self._files(before)
            if {p: sha256(v).hexdigest() for p, v in files.items()} != approval['files']:
                raise ValueError('Reviewed files differ from committed parent')
            original = files.get('AGENTS.md', b'')
            content = accepted_constraints(review, candidate_revision=before,
                contract_version=request.contract_version, original=original, entries=entries)
            intent_path = confined_path(review.root, self.path)
            head = git(workspace.path, 'rev-parse', 'HEAD').decode().strip()
            status = git(workspace.path, 'status', '--porcelain=v1', '-z', '--untracked-files=all').decode()
            # Only the recorded metadata write may be pending during recovery.
            if any(record[3:] != 'AGENTS.md' for record in status.split('\0') if record):
                raise ValueError('Unreviewed worktree changes block completion')
            for path, value in files.items():
                if path != 'AGENTS.md' and confined_path(workspace.path, path).read_bytes() != value:
                    raise ValueError('Reviewed source bytes changed')
            target = confined_path(workspace.path, 'AGENTS.md')
            actual = target.read_bytes() if target.exists() else b''
            if actual not in (original, content):
                raise ValueError('Unrelated managed-file edits block completion')
            identity = dict(request=wire, content_sha256=sha256(content).hexdigest(), before=before)
            if intent_path.exists():
                intent = json.loads(intent_path.read_bytes())
                if any(intent.get(k) != v for k, v in identity.items()):
                    raise ValueError('Completion intent changed on recovery')
                after = intent['after']
            else:
                if head != before or status:
                    raise ValueError('Completion requires the clean approved parent')
                after = self._build(before, content, content != original)
                intent = dict(identity, after=after)
                atomic_write(review.root, self.path, json.dumps(intent, sort_keys=True).encode())
            parents = git(workspace.path, 'rev-list', '--parents', '-n', '1', after).decode().split()
            changed = git(workspace.path, 'diff', '--name-only', before, after).decode().splitlines()
            if parents != [after, before] or any(p != 'AGENTS.md' for p in changed):
                raise ValueError('Completion revision is not metadata-only with exact approved parent')
            expected_files = dict(files)
            if content != original:
                expected_files['AGENTS.md'] = content
            if self._files(after) != expected_files:
                raise ValueError('Recorded completion tree differs from approved metadata')
            if head == before:
                self._publish(before, after)
            elif head != after:
                raise ValueError('Git state conflicts with completion intent')
            if changed:
                git(workspace.path, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                    'restore', '--source=' + after, '--staged', '--worktree', '--', 'AGENTS.md')
                if target.read_bytes() != content:
                    raise ValueError('Checkout altered accepted metadata bytes')
                files['AGENTS.md'] = content
            return review.finalize(request, parent_revision=before, completion_revision=after, files=files)
