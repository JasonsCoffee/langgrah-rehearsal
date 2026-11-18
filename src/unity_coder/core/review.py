"""Durable exact-candidate review; authentication belongs to the trusted host."""

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal

from .lifecycle import RunLifecycle
from .ownership import confined_path, portable_path
from .storage import atomic_write, file_guard
from .tdd import BehaviorEvidence, validate_behavior
from .verification import VerificationRequest, VerificationResult


def _wire(request: VerificationRequest) -> dict[str, object]:
    return json.loads(json.dumps(asdict(request)))


def _snapshot(files: Mapping[str, bytes]) -> dict[str, str]:
    return {portable_path(path): sha256(content).hexdigest() for path, content in files.items()}


@dataclass(frozen=True)
class ReviewPackage:
    request: VerificationRequest
    scope: Literal['code', 'visual']
    entries: tuple[str, ...]
    launch_instructions: str
    required_interactions: tuple[str, ...]
    visual_references: tuple[str, ...]
    placeholder_limitations: str

    def validate(self, request: VerificationRequest, files: Mapping[str, bytes]) -> None:
        if self.request != request or self.scope not in ('code', 'visual'):
            raise ValueError('Review guidance belongs to another candidate or scope')
        if (not self.launch_instructions.strip() or not self.placeholder_limitations.strip()
            or not self.required_interactions or any(not item.strip() for item in self.required_interactions)):
            raise ValueError('Review guidance is incomplete')
        if self.scope == 'visual' and (not self.entries or not self.visual_references):
            raise ValueError('Visual review requires entries and design references')
        for path in (*self.entries, *self.visual_references):
            if portable_path(path) not in files:
                raise ValueError('Review reference is outside the reviewed snapshot')


class ReviewGate:
    def __init__(self, lifecycle: RunLifecycle, *, authenticate_human: Callable[[str], str | None]) -> None:
        """The callback must authenticate a human session, never a model claim.

        Coding tools cannot expose this object or its callback. Credentials are
        transient and are never persisted in review records.
        """
        self.lifecycle = lifecycle
        self.authenticate = authenticate_human
        self.root = lifecycle.root
        self.path = lifecycle.prefix + "/review.json"
        self.guard = lifecycle.prefix + "/review.guard"

    def state(self) -> dict[str, object]:
        return json.loads(confined_path(self.root, self.path).read_bytes())

    def _write(self, record: dict[str, object]) -> None:
        atomic_write(self.root, self.path, json.dumps(record, sort_keys=True).encode())

    def _identity(self, request: VerificationRequest) -> None:
        if (request.run_id != self.lifecycle.run_id or request.contract_version != self.lifecycle.contract_version
            or request.contract_sha256 != self.lifecycle.contract_sha256):
            raise ValueError("Review belongs to another run/contract")

    def offer(self, evidence: VerificationResult, files: Mapping[str, bytes], *,
              evidence_refs: tuple[str, ...], package: ReviewPackage | None = None) -> dict[str, object]:
        request = evidence.request
        self._identity(request)
        if (evidence.status != "passed" or evidence.gate != "tests" or not evidence.full_suite_verified
            or not evidence.behavioral or not request.full_suite or evidence.test_result is None
            or evidence.violations or evidence.failed_tests or not evidence_refs):
            raise ValueError("Review requires runnable full-suite verified evidence")
        validate_behavior(BehaviorEvidence(request.candidate_revision, request.test_selection, evidence.test_result),
                          request.test_selection)
        if evidence.test_result.failed:
            raise ValueError("Review requires passing tests")
        for ref in evidence_refs:
            confined_path(self.root, ref)
        record: dict[str, object] = {"request": _wire(request), "candidate_revision": request.candidate_revision,
            "files": _snapshot(files), "evidence_refs": list(evidence_refs), "decision": "pending"}
        if package is not None:
            package.validate(request, files)
            record['package'] = json.loads(json.dumps(asdict(package)))
        with file_guard(self.root, self.guard):
            if confined_path(self.root, self.path).exists():
                prior = self.state()
                if prior["request"] == record["request"]:
                    if prior.get('package') != record.get('package'):
                        raise ValueError('Review guidance changed without fresh verification')
                    if prior["files"] != record["files"]:
                        raise ValueError("Candidate bytes changed without a new identity")
                    if prior["decision"] != "pending":
                        raise ValueError("Reviewed request requires a fresh verification request")
                else:
                    if prior["decision"] == "contract":
                        raise ValueError("Contract rework requires the Architect's next version")
                    old = sha256(json.dumps(prior, sort_keys=True).encode()).hexdigest()
                    atomic_write(self.root, self.lifecycle.prefix + f"/reviews/{old}.json", json.dumps(prior, sort_keys=True).encode())
            self._write(record)
            return self.lifecycle.finish("awaiting_human_review", candidate_revision=request.candidate_revision,
                                         reason="Full-suite candidate awaits human review", evidence_refs=evidence_refs)

    def decide(self, credential: str, request: VerificationRequest,
               decision: Literal["accept", "implementation", "contract"], *,
               findings: tuple[str, ...]) -> dict[str, object]:
        reviewer = self.authenticate(credential)
        if not reviewer:
            raise ValueError("Authenticated human review required")
        self._identity(request)
        if decision not in ("accept", "implementation", "contract") or (decision != "accept" and not findings):
            raise ValueError("Review needs a decision and actionable findings")
        if decision == "accept" and findings:
            raise ValueError("Unresolved findings cannot be accepted")
        with file_guard(self.root, self.guard):
            record = self.state()
            if record["request"] != _wire(request) or record["decision"] != "pending":
                raise ValueError("Stale or already consumed human review")
            action = {"accept": "finalize", "implementation": "repair", "contract": "rework"}[decision]
            record.update(decision=decision, action=action, reviewer=reviewer, findings=list(findings),
                          reviewed_utc=datetime.now(timezone.utc).isoformat(), contract_version=request.contract_version)
            self._write(record)
            return record

    def finalize(self, request: VerificationRequest, *, parent_revision: str,
                 completion_revision: str, files: Mapping[str, bytes]) -> dict[str, object]:
        self._identity(request)
        with file_guard(self.root, self.guard):
            record = self.state()
            if record["request"] != _wire(request) or record["decision"] != "accept":
                raise ValueError("No human approval for this candidate")
            if parent_revision != request.candidate_revision or not completion_revision:
                raise ValueError("Completion does not descend from approved parent")
            before = dict(record["files"])
            after = _snapshot(files)
            # Only the accepted managed-constraints file may differ. Its block
            # provenance and preservation are enforced by the constraint writer.
            before.pop("AGENTS.md", None)
            after.pop("AGENTS.md", None)
            if before != after:
                raise ValueError("Completion changes reviewed content")
            result: dict[str, object] = {"format_version": 1, "run_id": request.run_id,
                "contract_version": request.contract_version, "contract_sha256": request.contract_sha256,
                "outcome": "pass", "approved_parent": parent_revision, "candidate_revision": completion_revision,
                "reviewer": record["reviewer"], "review_ref": self.path, "evidence_refs": record["evidence_refs"]}
            atomic_write(self.root, self.lifecycle.prefix + "/result.json", json.dumps(result, sort_keys=True).encode())
            return result
