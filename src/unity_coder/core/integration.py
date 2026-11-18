"""Explicit shared evidence and bounded, per-owner coordinated repair plans."""

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Literal, Mapping, TypeVar

from .contracts import Contract
from .ownership import within
from .verification import VerificationResult


@dataclass(frozen=True)
class UnitDecision:
    defect_class: str
    repair_paths: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class SharedFailure:
    evidence_id: str
    request_id: str
    contract_sha256: str
    candidate_revision: str
    failed_tests: tuple[str, ...]
    test_authors: tuple[str, ...]
    implementing_units: tuple[str, ...]
    patch_ids: Mapping[str, str]


@dataclass(frozen=True)
class UnitRoute:
    defect_class: Literal["implementation", "contract"]
    evidence_id: str
    repair_paths: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class RepairRouting:
    units: Mapping[str, UnitRoute]

    @property
    def can_dispatch(self) -> bool:
        return bool(self.units) and all(u.defect_class == "implementation" for u in self.units.values())


def shared_failure(contract: Contract, result: VerificationResult,
                   patch_ids: Mapping[str, str]) -> SharedFailure:
    """Preserve relationships without attributing blame from a test name."""
    if result.status != "failed" or not result.behavioral or not result.failed_tests:
        raise ValueError("Shared failure requires failed behavioral evidence")
    if result.request.contract_sha256 != contract.sha256:
        raise ValueError("Failure belongs to another contract")
    links = [t for t in contract.test_links if t.test_id in result.failed_tests]
    if {t.test_id for t in links} != set(result.failed_tests):
        raise ValueError("Unmapped failing tests")
    authors = tuple(sorted({t.author_unit for t in links}))
    implementers = tuple(sorted({u for t in links for u in t.implementing_units}))
    if any(not patch_ids.get(u) for u in implementers):
        raise ValueError("Missing contributing revision identity")
    contributors = {u: patch_ids[u] for u in implementers}
    identity = {"request": result.request.request_id, "contract": contract.sha256,
                "candidate": result.request.candidate_revision, "tests": sorted(result.failed_tests),
                "patches": contributors}
    evidence_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return SharedFailure(evidence_id, result.request.request_id, contract.sha256,
                         result.request.candidate_revision, result.failed_tests, authors,
                         implementers, MappingProxyType(contributors))


def route_repairs(contract: Contract, evidence: SharedFailure, decisions: Mapping[str, UnitDecision], *,
                  frozen_paths: tuple[str, ...] = ()) -> RepairRouting:
    if evidence.contract_sha256 != contract.sha256:
        raise ValueError("Routing evidence belongs to another contract")
    if set(decisions) - set(evidence.implementing_units):
        raise ValueError("Judge supplied unrelated unit decisions")
    routes: dict[str, UnitRoute] = {}
    for unit_id in evidence.implementing_units:
        decision = decisions.get(unit_id)
        if decision is None or decision.defect_class not in ("implementation", "contract") or not decision.rationale.strip():
            routes[unit_id] = UnitRoute("contract", evidence.evidence_id, (), "Ambiguous or missing repair partition")
            continue
        if decision.defect_class == "contract":
            routes[unit_id] = UnitRoute("contract", evidence.evidence_id, (), decision.rationale)
            continue
        valid = bool(decision.repair_paths) and len(set(decision.repair_paths)) == len(decision.repair_paths)
        try:
            valid = valid and all(contract.owner_of(p) == unit_id and not any(
                within(p, f, contract._rules) for f in frozen_paths
            ) for p in decision.repair_paths)
        except ValueError:
            valid = False
        if valid:
            routes[unit_id] = UnitRoute("implementation", evidence.evidence_id, decision.repair_paths, decision.rationale)
        else:
            routes[unit_id] = UnitRoute("contract", evidence.evidence_id, (), "No repair partition within frozen ownership")
    return RepairRouting(MappingProxyType(routes))


EvidenceValue = TypeVar("EvidenceValue")


def invalidate_dependents(contract: Contract, changed: tuple[str, ...],
                          evidence: Mapping[str, EvidenceValue]) -> dict[str, EvidenceValue]:
    """Invalidate transitive consumers and participants of affected shared tests."""
    active = {u.id: u for u in contract.units if u.status == "active"}
    if not set(changed) <= active.keys():
        raise ValueError("Unknown changed unit")
    invalid = set(changed)
    while True:
        before = invalid.copy()
        for unit in active.values():
            if invalid.intersection(unit.depends_on):
                invalid.add(unit.id)
        for link in contract.test_links:
            if invalid.intersection(link.implementing_units):
                invalid.update(link.implementing_units)
        if invalid == before:
            return {u: e for u, e in evidence.items() if u not in invalid}


class RepairRounds:
    """Idempotent round arithmetic; persistence is supplied by the run journal."""

    def __init__(self) -> None:
        self._failed_attempts: dict[str, int] = {}
        self._rounds: dict[str, frozenset[str]] = {}

    @property
    def failed_attempts(self) -> Mapping[str, int]:
        return MappingProxyType(self._failed_attempts)

    def charge_failure(self, round_id: str, participants: tuple[str, ...]) -> None:
        group = frozenset(participants)
        if not round_id or not group or len(group) != len(participants):
            raise ValueError("Invalid repair round")
        if round_id in self._rounds:
            if group != self._rounds[round_id]:
                raise ValueError("Repair round identity changed")
            return
        self._rounds[round_id] = group
        for unit_id in group:
            self._failed_attempts[unit_id] = self._failed_attempts.get(unit_id, 0) + 1
