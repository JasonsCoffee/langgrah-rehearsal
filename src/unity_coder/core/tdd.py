"""Independent test preparation and a global freeze barrier for implementation."""

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .contracts import Contract, Unit
from .evidence import TestResult
from .ownership import PathRules, confined_path, validate_owned_path
from .storage import atomic_write


@dataclass(frozen=True)
class BehaviorEvidence:
    snapshot: str
    requested: tuple[str, ...]
    result: TestResult
    failure_kind: str = "assertion"


@dataclass(frozen=True)
class UnitTDD:
    stage: str
    baseline: BehaviorEvidence | None = None
    coverage_review: str = ""
    already_satisfied: bool = False
    failed_attempts: int = 0
    preparation_attempts: int = 0
    green_snapshot: str | None = None
    accepted_snapshot: str | None = None
    refactor_reason: str = ""


def validate_behavior(evidence: BehaviorEvidence, required: tuple[str, ...]) -> None:
    """Require actual, unambiguous execution of every selected acceptance test."""
    result = evidence.result
    if not evidence.snapshot or not required or not evidence.requested:
        raise ValueError("Missing snapshot or test selection")
    if result.operational_error or evidence.failure_kind != "assertion" or result.failure_kind != "assertion":
        raise ValueError("Nonbehavioral evidence cannot establish TDD")
    for values in (evidence.requested, result.discovered, result.executed, result.passed, result.failed):
        if len(values) != len(set(values)):
            raise ValueError("Duplicate test evidence")
    requested, executed = set(evidence.requested), set(result.executed)
    if not set(required) <= requested <= set(result.discovered) or requested != executed:
        raise ValueError("Missing or unexpected test execution")
    if result.skipped or result.inconclusive or set(result.passed) & set(result.failed):
        raise ValueError("Skipped, inconclusive, or contradictory results")
    if set(result.passed) | set(result.failed) != executed:
        raise ValueError("Incomplete test outcomes")


class TDDCoordinator:
    def __init__(self, contract: Contract, root: Path, rules: PathRules, *,
                 test_config_paths: tuple[str, ...] = (), max_preparation_attempts: int = 3,
                 protected_paths: tuple[str, ...] = ()) -> None:
        if max_preparation_attempts < 1:
            raise ValueError("Preparation allowance must be positive")
        self.contract, self.root, self.rules = contract, root, rules
        self.units = MappingProxyType({u.id: u for u in contract.units if u.status == "active"})
        self._states = {u.id: UnitTDD("test_authoring" if u.role == "test" else "awaiting_red") for u in self.units.values()}
        self._reviews: dict[str, str] = {}
        self._frozen_hashes: dict[str, str] | None = None
        self._test_config_paths = test_config_paths
        self._protected = protected_paths + (contract.spec.path, contract.presentation_ref.path,
                                             contract.coding_profile_ref.path, contract.environment_ref.path)
        self._max_preparation_attempts = max_preparation_attempts
        self._usage: dict[str, tuple[int, int]] = {}
        self._baseline_test_hashes: dict[str, dict[str, str]] = {}
        self._green_files: dict[str, dict[str, bytes | None]] = {}

    @property
    def frozen(self) -> bool:
        return self._frozen_hashes is not None

    @property
    def model_input_tokens(self) -> int:
        return sum(v[0] for v in self._usage.values())

    @property
    def model_output_tokens(self) -> int:
        return sum(v[1] for v in self._usage.values())

    def state(self, unit_id: str) -> UnitTDD:
        try:
            return self._states[unit_id]
        except KeyError as exc:
            raise ValueError("Unknown active unit") from exc

    def _unit(self, unit_id: str, role: str) -> Unit:
        self.state(unit_id)
        unit = self.units[unit_id]
        if unit.role != role:
            raise ValueError("Incorrect unit role")
        return unit

    def approve_tests(self, unit_id: str, review: str) -> None:
        self._unit(unit_id, "test")
        if self.frozen or not review.strip() or self.state(unit_id).stage == "preparation_exhausted":
            raise ValueError("Tests cannot be approved in this state")
        self._reviews[unit_id] = review
        self._states[unit_id] = replace(self.state(unit_id), stage="test_reviewed")

    def record_baseline(self, unit_id: str, evidence: BehaviorEvidence, *, coverage_review: str = "") -> None:
        unit = self._unit(unit_id, "impl")
        if self.frozen:
            raise ValueError("Baseline is frozen")
        validate_behavior(evidence, unit.acceptance)
        failed = bool(set(unit.acceptance) & set(evidence.result.failed))
        if not failed and not coverage_review.strip():
            raise ValueError("Already-passing baseline needs independent coverage review")
        self._states[unit_id] = replace(self.state(unit_id), baseline=evidence, coverage_review=coverage_review,
                                       already_satisfied=not failed, stage="red_evidenced")
        self._baseline_test_hashes[unit_id] = self._test_hashes()

    def _test_hashes(self) -> dict[str, str]:
        paths = self._test_config_paths + tuple(p for u in self.units.values() if u.role == "test" for p in u.owns)
        return {p: self._hash(p) for p in paths}

    def freeze(self) -> None:
        if self.frozen:
            self.assert_frozen()
            return
        snapshots: set[str] = set()
        for unit in self.units.values():
            if unit.role == "test":
                if unit.id not in self._reviews:
                    raise ValueError("Every test author requires validity/coverage review")
            else:
                baseline = self.state(unit.id).baseline
                if baseline is None:
                    raise ValueError("Every implementation unit requires baseline evidence")
                snapshots.add(baseline.snapshot)
        if len(snapshots) != 1:
            raise ValueError("Baseline evidence must describe the same snapshot")
        current = self._test_hashes()
        if any(hashes != current for hashes in self._baseline_test_hashes.values()):
            raise ValueError("Tests changed after baseline verification")
        self._frozen_hashes = current

    def _hash(self, path: str) -> str:
        try:
            return hashlib.sha256(confined_path(self.root, path).read_bytes()).hexdigest()
        except OSError as exc:
            raise ValueError(f"Missing frozen input: {path}") from exc

    def assert_frozen(self) -> None:
        if self._frozen_hashes is None:
            raise ValueError("Implementation cannot run before global test freeze")
        if any(self._hash(p) != h for p, h in self._frozen_hashes.items()):
            raise ValueError("Frozen test or configuration changed")
        for ref in (self.contract.spec, self.contract.presentation_ref,
                    self.contract.coding_profile_ref, self.contract.environment_ref):
            if self._hash(ref.path) != ref.sha256:
                raise ValueError("Frozen contract input changed")

    def begin(self, unit_id: str) -> None:
        self.assert_frozen()
        unit = self._unit(unit_id, "impl")
        if self.state(unit_id).stage != "red_evidenced":
            raise ValueError("Unit is not ready for Green coding")
        for dependency in unit.depends_on:
            if not self.dependency_ready(unit_id,dependency):
                raise ValueError("Dependency lacks a frozen interface or completed implementation")
        self._states[unit_id] = replace(self.state(unit_id), stage="green_coding")

    def dependency_ready(self, unit_id: str, dependency: str) -> bool:
        if self.state(dependency).stage == "complete" or self.units[dependency].interfaces:
            return True
        return self.state(dependency).stage == "pending_shared_verification" and any(
            {unit_id,dependency} <= set(link.implementing_units) for link in self.contract.test_links)

    def validate_patch(self, unit_id: str, changes: Mapping[str, bytes | None]) -> None:
        unit = self.units[unit_id]
        if self.frozen:
            self.assert_frozen()
            if unit.role == "test":
                raise ValueError("Test authors cannot modify frozen tests")
        elif unit.role == "impl":
            raise ValueError("Implementation patch before freeze")
        frozen = {self.rules.normalise_path(p) for p in (self._frozen_hashes or {})}
        for path in changes:
            key = validate_owned_path(path, (self.contract.module_root,) if unit.role == "impl" else self.contract.test_roots,
                                      self.root, self.rules, self._protected)
            if key in frozen:
                raise ValueError("Patch modifies frozen test/configuration")
            if not self.rules.is_generated(path) and self.contract.owner_of(path) != unit_id:
                raise ValueError("Patch modifies another unit's ownership")

    def record_green(self, unit_id: str, evidence: BehaviorEvidence) -> None:
        self.assert_frozen()
        unit = self._unit(unit_id, "impl")
        if self.state(unit_id).stage not in ("green_coding", "pending_shared_verification"):
            raise ValueError("Unexpected Green evidence")
        validate_behavior(evidence, unit.acceptance)
        if evidence.result.failed:
            self._states[unit_id] = replace(self.state(unit_id), failed_attempts=self.state(unit_id).failed_attempts + 1)
            return
        self._states[unit_id] = replace(self.state(unit_id), stage="green_verified", green_snapshot=evidence.snapshot)
        self._green_files[unit_id] = {}
        for path in unit.owns:
            target = confined_path(self.root, path)
            self._green_files[unit_id][path] = target.read_bytes() if target.is_file() else None

    def begin_refactor(self, unit_id: str) -> None:
        self.assert_frozen()
        if self.state(unit_id).stage != "green_verified":
            raise ValueError("Refactor requires verified Green")
        self._states[unit_id] = replace(self.state(unit_id), stage="refactor_coding")

    def finish_refactor(self, unit_id: str, evidence: BehaviorEvidence | None = None, *, reason: str = "") -> str | None:
        self.assert_frozen()
        unit = self._unit(unit_id, "impl")
        state = self.state(unit_id)
        if evidence is None:
            if state.stage != "green_verified" or not reason.strip():
                raise ValueError("No-change refactor requires Green and a reason")
            self._states[unit_id] = replace(state, stage="complete", accepted_snapshot=state.green_snapshot, refactor_reason=reason)
            return None
        if state.stage != "refactor_coding":
            raise ValueError("Unexpected Refactor evidence")
        validate_behavior(evidence, unit.acceptance)
        if evidence.result.failed:
            # The coordinator root is its isolated integration workspace. Never
            # restore peer ownership; durable crash reconciliation arrives in Phase 8.
            for path, content in self._green_files[unit_id].items():
                target = confined_path(self.root, path)
                if content is None:
                    target.unlink(missing_ok=True)
                else:
                    atomic_write(self.root, path, content)
            self._states[unit_id] = replace(state, stage="green_verified", failed_attempts=state.failed_attempts + 1)
            return state.green_snapshot
        self._states[unit_id] = replace(state, stage="complete", accepted_snapshot=evidence.snapshot)
        return None

    def pending_shared(self, unit_id: str) -> None:
        self.assert_frozen()
        if self.state(unit_id).stage != "green_coding":
            raise ValueError("Only coded units can await shared verification")
        self._states[unit_id] = replace(self.state(unit_id), stage="pending_shared_verification")

    def record_group_green(self, unit_ids: tuple[str, ...], evidence: BehaviorEvidence) -> None:
        self.assert_frozen()
        if not unit_ids or len(set(unit_ids)) != len(unit_ids):
            raise ValueError("Invalid shared group")
        participants = set(unit_ids)
        for link in self.contract.test_links:
            if participants & set(link.implementing_units) and not set(link.implementing_units) <= participants:
                raise ValueError("Missing shared verification participant")
        required = tuple(dict.fromkeys(t for u in unit_ids for t in self._unit(u, "impl").acceptance))
        validate_behavior(evidence, required)
        if any(self.state(u).stage not in ("green_coding", "pending_shared_verification") for u in unit_ids):
            raise ValueError("Shared participants are not ready")
        for unit_id in unit_ids:
            self.record_green(unit_id, evidence)

    def record_preparation_failure(self, unit_id: str) -> None:
        self._unit(unit_id, "test")
        if self.frozen:
            raise ValueError("Frozen test defects require contract rework")
        state = self.state(unit_id)
        count = state.preparation_attempts + 1
        exhausted = count >= self._max_preparation_attempts
        self._states[unit_id] = replace(state, preparation_attempts=count,
                                       stage="preparation_exhausted" if exhausted else "test_authoring")
        self._reviews.pop(unit_id, None)
        if exhausted:
            raise ValueError("Test preparation allowance exhausted")

    def record_model_usage(self, call_id: str, input_tokens: int, output_tokens: int) -> None:
        if not call_id or any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
            raise ValueError("Invalid call usage")
        usage = (input_tokens, output_tokens)
        if call_id in self._usage and self._usage[call_id] != usage:
            raise ValueError("Conflicting usage for an existing call")
        self._usage[call_id] = usage
