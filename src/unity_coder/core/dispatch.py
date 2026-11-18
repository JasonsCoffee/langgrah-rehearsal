"""Parallel agent calls produce validated candidates, never shared-tree writes."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping

from .contracts import Unit
from .tdd import TDDCoordinator


@dataclass(frozen=True)
class Candidate:
    unit_id: str
    base_revision: str
    changes: Mapping[str, bytes | None]
    violation: str | None = None


def ready_units(coordinator: TDDCoordinator) -> tuple[str, ...]:
    if coordinator.frozen:
        coordinator.assert_frozen()
    ready: list[str] = []
    for unit in coordinator.units.values():
        state = coordinator.state(unit.id)
        if not coordinator.frozen:
            if unit.role == "test" and state.stage == "test_authoring" and all(
                coordinator.state(d).stage == "test_reviewed" for d in unit.depends_on
            ):
                ready.append(unit.id)
        elif unit.role == "impl" and state.stage == "red_evidenced" and all(
            coordinator.dependency_ready(unit.id,d) for d in unit.depends_on
        ):
            ready.append(unit.id)
    return tuple(ready)


def dispatch_parallel(coordinator: TDDCoordinator,
                      agent: Callable[[Unit], Mapping[str, bytes | None]]) -> tuple[Candidate, ...]:
    selected = ready_units(coordinator)
    if not selected:
        return ()
    for unit_id in selected:
        if coordinator.units[unit_id].role == "impl":
            coordinator.begin(unit_id)

    def code(unit_id: str) -> Candidate:
        state = coordinator.state(unit_id)
        base = state.baseline.snapshot if state.baseline is not None else coordinator.contract.sha256
        try:
            changes = dict(agent(coordinator.units[unit_id]))
            coordinator.validate_patch(unit_id, changes)
            return Candidate(unit_id, base, MappingProxyType(changes))
        except Exception as exc:
            return Candidate(unit_id, base, MappingProxyType({}), str(exc))

    with ThreadPoolExecutor(max_workers=len(selected), thread_name_prefix="coding-unit") as pool:
        return tuple(pool.map(code, selected))
