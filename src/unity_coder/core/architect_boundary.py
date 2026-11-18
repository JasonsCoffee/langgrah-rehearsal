"""Read-only planning provenance and trusted local executor handoff.

Run state must be outside coder-writable scopes. This boundary checks persisted
receipts; it neither authenticates humans nor substitutes for CandidateCompletion.
"""

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

from .contracts import ArtifactRef, Contract, _object, _text
from .journal import run_prefix
from .ownership import confined_path, portable_path
from .progress import ProgressStore
from .storage import atomic_write, file_guard


def _relative(root: Path, value: object) -> str:
    path = Path(_text(value))
    if path.is_absolute():
        try:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            raise ValueError("Planning path escapes selected root") from None
    else:
        relative = _text(value)
    confined_path(root, relative)
    return portable_path(relative)


def _reference(root: Path, value: object) -> ArtifactRef:
    relative = _relative(root, value)
    try:
        content = confined_path(root, relative).read_bytes()
    except OSError:
        raise ValueError(f"Missing planning source: {relative}") from None
    return ArtifactRef(relative, sha256(content).hexdigest())


@dataclass(frozen=True)
class PlanningTask:
    task_ref: str
    description: str
    done: bool
    source_path: str
    line: int


@dataclass(frozen=True)
class PlanningContext:
    schema: str
    change: str
    artifacts: tuple[tuple[str, tuple[ArtifactRef, ...]], ...]
    sources: tuple[tuple[str, ArtifactRef], ...]
    tasks: tuple[PlanningTask, ...]

    def to_dict(self) -> dict[str, object]:
        return {"format_version": 1, "schema": self.schema, "change": self.change,
                "artifacts": {key: [asdict(ref) for ref in refs] for key, refs in self.artifacts},
                "sources": {key: asdict(ref) for key, ref in self.sources},
                "tasks": [asdict(task) for task in self.tasks]}

    def validate(self, root: Path) -> None:
        refs = [ref for _, group in self.artifacts for ref in group]
        refs.extend(ref for _, ref in self.sources)
        for ref in refs:
            if _reference(root, ref.path) != ref:
                raise ValueError(f"Planning source changed: {ref.path}")


def discover_context(root: Path, instructions: Mapping[str, object], *,
                     sources: Mapping[str, str]) -> PlanningContext:
    """Consume pinned CLI apply JSON; artifact names belong to its active schema.

    Additional design/wiki/rule sources are explicitly selected by the Architect.
    Prompt context/guidance is not copied into a portable execution artifact.
    """
    selected = instructions.get("root")
    if not isinstance(selected, dict) or Path(_text(selected.get("path"))).resolve() != root.resolve():
        raise ValueError("Existing selected planning root required")
    if instructions.get("state") != "ready" or instructions.get("missingArtifacts"):
        raise ValueError("Planning is not ready for delegated apply")
    schema, change = _text(instructions.get("schemaName")), _text(instructions.get("changeName"))
    artifacts = []
    for key, paths in _object(instructions.get("contextFiles")).items():
        if not isinstance(paths, list) or not paths:
            raise ValueError("Artifact requires concrete context files")
        artifacts.append((key, tuple(_reference(root, path) for path in paths)))
    if not artifacts:
        raise ValueError("No schema context discovered")
    tracked_paths = {ref.path for _, refs in artifacts for ref in refs}
    tasks = []
    seen: set[str] = set()
    raw_tasks = instructions.get("tasks")
    if not isinstance(raw_tasks, list):
        raise ValueError("Schema task list required")
    for raw in raw_tasks:
        task = _object(raw)
        task_ref = change + ":" + _text(task.get("id"))
        description = _text(task.get("description"))
        relative = _relative(root, task.get("sourcePath"))
        line, done = task.get("line"), task.get("done")
        if task_ref in seen or relative not in tracked_paths:
            raise ValueError("Duplicate task or task outside discovered context")
        if type(line) is not int or line < 1 or type(done) is not bool:
            raise ValueError("Invalid task location or completion flag")
        lines = confined_path(root, relative).read_text(encoding="utf-8").splitlines()
        match = re.fullmatch(r"\s*[-*+] \[([ xX])\]\s+(.+?)\s*", lines[line - 1]) if line <= len(lines) else None
        if not match or match[2] != description or (match[1] != " ") != done:
            raise ValueError("Stale task location; rediscover apply instructions")
        seen.add(task_ref)
        tasks.append(PlanningTask(task_ref, description, done, relative, line))
    return PlanningContext(schema, change, tuple(sorted(artifacts)),
                           tuple((key, _reference(root, path)) for key, path in sorted(sources.items())),
                           tuple(tasks))


class ArchitectBoundary:
    def __init__(self, planning_root: Path, state_root: Path, run_id: str,
                 contract: Contract, context: PlanningContext) -> None:
        self.planning_root, self.state_root = planning_root, state_root
        self.run_id, self.contract, self.context = run_id, contract, context
        self.prefix = run_prefix(run_id)
        context.validate(planning_root)
        known = {task.task_ref for task in context.tasks}
        if any(link.task_ref not in known for link in contract.task_links):
            raise ValueError("Contract references an undiscovered planning task")
        identity = {"format_version": 1, "run_id": run_id, "contract_version": contract.contract_version,
                    "contract_sha256": contract.sha256, "context": context.to_dict()}
        with file_guard(state_root, self.prefix + "/boundary.guard"):
            path = confined_path(state_root, self.prefix + "/invocation.json")
            if path.exists() and json.loads(path.read_bytes()) != identity:
                raise ValueError("Invocation identity or planning provenance changed")
            atomic_write(state_root, self.prefix + "/invocation.json", json.dumps(identity, sort_keys=True).encode())

    def _read(self, name: str) -> dict[str, object] | None:
        path = confined_path(self.state_root, self.prefix + "/" + name + ".json")
        return _object(json.loads(path.read_bytes())) if path.exists() else None

    def _identity(self, record: Mapping[str, object]) -> None:
        if (record.get("run_id") != self.run_id or type(record.get("contract_version")) is not int
            or record.get("contract_version") != self.contract.contract_version
            or record.get("contract_sha256") != self.contract.sha256):
            raise ValueError("Run or contract identity mismatch")

    def observe(self) -> dict[str, object]:
        self.context.validate(self.planning_root)
        progress = ProgressStore(self.state_root, self.run_id, contract_version=self.contract.contract_version,
                                 contract_sha256=self.contract.sha256).status()
        result = self._read("result")
        action, accepted = "resume" if progress else "start", False
        if result is not None:
            self._identity(result)
            if type(result.get("format_version")) is not int or result["format_version"] != 1:
                raise ValueError("Unsupported result format")
            outcome = result.get("outcome")
            if outcome not in ("operational", "cancelled", "rework", "abandon", "awaiting_human_review", "pass"):
                raise ValueError("Unknown run outcome")
            refs = result.get("evidence_refs")
            if not isinstance(refs, list):
                raise ValueError("Result requires evidence references")
            for ref in refs:
                confined_path(self.state_root, _text(ref))
            action = "wait" if outcome == "awaiting_human_review" else "ended"
            if outcome in ("awaiting_human_review", "pass"):
                record = self._read("review")
                if record is not None:
                    request = _object(record.get("request"))
                    self._identity(request)
                    expected = result.get("approved_parent") if outcome == "pass" else result.get("candidate_revision")
                    if not expected or request.get("candidate_revision") != expected or record.get("candidate_revision") != expected:
                        raise ValueError("Stale review candidate")
                    decision = record.get("decision")
                    if decision not in ("pending", "accept", "implementation", "contract"):
                        raise ValueError("Unknown review decision")
                    if decision != "pending":
                        _text(record.get("reviewer"))
                    action = {"pending": "wait", "accept": "finalize", "implementation": "repair", "contract": "rework"}[decision]
                if outcome == "pass":
                    if (record is None or record.get("decision") != "accept"
                        or record.get("reviewer") != result.get("reviewer")
                        or result.get("review_ref") != self.prefix + "/review.json"
                        or not result.get("candidate_revision")):
                        raise ValueError("Accepted pass requires matching human review")
                    accepted, action = True, "ended"
        mapped = {link.task_ref for link in self.contract.task_links}
        return {"result": result, "progress": progress, "next_action": action,
                "eligible_tasks": sorted(mapped) if accepted else [],
                "unmapped_tasks": [task.task_ref for task in self.context.tasks if task.task_ref not in mapped]}

    def invoke(self, executor: Callable[[str], object]) -> dict[str, object]:
        """Blocking trusted-host callback; reconnect never authorizes another run.

        The executor owns RunLease, verification, budgets and candidate completion.
        Its return value is deliberately ignored: only durable receipts are read.
        """
        report = self.observe()
        action = report["next_action"]
        if action in ("start", "resume", "repair", "finalize"):
            executor(str(action))
        return self.observe()
