"""Deterministic bounded retry trends, independent of model judgments."""

from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, TypeVar

from .contracts import Contract
from .integration import invalidate_dependents
from .ownership import confined_path
from .storage import atomic_write


@dataclass(frozen=True)
class Observation:
    gate: str
    failing: tuple[str, ...]
    selection: tuple[str, ...] = ("Test",)
    environment: str = "env"
    contract_sha256: str = "contract"
    baseline_sha256: str = "baseline"
    message: str = ""


def classify(previous: Observation | None, current: Observation) -> str | None:
    rank = {"ownership": 0, "conformance": 1, "compile": 2, "tests": 3}
    if current.gate not in rank:
        raise ValueError("Unknown verification gate")
    if previous is None:
        return "RED"
    if (set(previous.selection), previous.environment, previous.contract_sha256, previous.baseline_sha256) != (
        set(current.selection), current.environment, current.contract_sha256, current.baseline_sha256
    ):
        return None
    if rank[current.gate] != rank[previous.gate]:
        return "PROGRESSING" if rank[current.gate] > rank[previous.gate] else "REGRESSED"
    before, after = set(previous.failing), set(current.failing)
    if before == after:
        return "STALLED"
    return "PROGRESSING" if after < before else "REGRESSED"


@dataclass(frozen=True)
class Attempt:
    stage: str
    trend: str | None
    observation: Observation


@dataclass(frozen=True)
class RetryState:
    failed_attempts: int = 0
    regressions: int = 0
    previous: Observation | None = None
    history: tuple[Attempt, ...] = ()
    escalated: bool = False


@dataclass(frozen=True)
class RetryAction:
    kind: str
    defect_class: str | None = None
    trend: str | None = None


class RetryPolicy:
    def __init__(self, *, max_attempts: int = 3, states: Mapping[str, RetryState] | None = None) -> None:
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError("Repair allowance must be positive")
        self.max_attempts = max_attempts
        self._states = dict(states or {})

    def state(self, unit_id: str) -> RetryState:
        return self._states.get(unit_id, RetryState())

    def evaluate(self, unit_id: str, observation: Observation | None, *,
                 judge_class: str = "implementation", passed: bool = False,
                 expected_red: bool = False, stage: str = "green") -> RetryAction:
        state = self.state(unit_id)
        if not unit_id or state.escalated:
            raise ValueError("Unit requires contract rework before further attempts")
        if expected_red:
            if passed or observation is None or observation.gate != "tests" or not observation.failing:
                raise ValueError("Expected Red requires behavioral assertion failures")
            return RetryAction("baseline")
        if passed:
            if observation is not None and observation.failing:
                raise ValueError("Passing evidence contains failures")
            previous = observation or (replace(state.previous, gate="tests", failing=()) if state.previous else None)
            self._states[unit_id] = replace(state, previous=previous)
            return RetryAction("pass")
        if observation is None or not observation.failing or judge_class not in ("implementation", "contract"):
            raise ValueError("Failure requires normalized identities and a valid per-unit judgment")
        trend = classify(state.previous, observation)
        count = state.failed_attempts + 1
        regressions = state.regressions + int(trend == "REGRESSED")
        escalate = judge_class == "contract" or trend == "STALLED" or count >= self.max_attempts or regressions >= 2
        self._states[unit_id] = RetryState(count, regressions, observation,
                                          state.history + (Attempt(stage, trend, observation),), escalate)
        if trend == "REGRESSED":
            return RetryAction("restore_escalate" if escalate else "restore_retry", "contract" if escalate else "implementation", trend)
        if escalate:
            return RetryAction("escalate", "contract", trend)
        if trend is None:
            return RetryAction("review")
        return RetryAction("retry", "implementation", trend)


@dataclass(frozen=True)
class OwnedSnapshot:
    snapshot_id: str
    unit_id: str
    contract_sha256: str
    files: Mapping[str, bytes | None]


def capture_owned(root: Path, contract: Contract, unit_id: str, snapshot_id: str) -> OwnedSnapshot:
    unit = next((u for u in contract.units if u.id == unit_id and u.status == "active" and u.role == "impl"), None)
    if unit is None or not snapshot_id:
        raise ValueError("Invalid snapshot owner or identity")
    files: dict[str, bytes | None] = {}
    for path in unit.owns:
        target = confined_path(root, path)
        files[path] = target.read_bytes() if target.is_file() else None
    return OwnedSnapshot(snapshot_id, unit_id, contract.sha256, MappingProxyType(files))


Proof = TypeVar("Proof")


def restore_owned(root: Path, contract: Contract, snapshot: OwnedSnapshot,
                  evidence: Mapping[str, Proof]) -> dict[str, Proof]:
    if snapshot.contract_sha256 != contract.sha256:
        raise ValueError("Snapshot belongs to another contract")
    unit = next((u for u in contract.units if u.id == snapshot.unit_id and u.status == "active" and u.role == "impl"), None)
    if unit is None or set(snapshot.files) != set(unit.owns):
        raise ValueError("Snapshot does not exactly match owned paths")
    for path in snapshot.files:
        confined_path(root, path)
        if contract.owner_of(path) != snapshot.unit_id:
            raise ValueError("Snapshot ownership changed")
    for path, content in snapshot.files.items():
        if content is None:
            confined_path(root, path).unlink(missing_ok=True)
        else:
            atomic_write(root, path, content)
    return invalidate_dependents(contract, (snapshot.unit_id,), evidence)
