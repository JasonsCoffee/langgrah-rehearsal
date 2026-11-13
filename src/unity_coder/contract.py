"""Contract loading and file-ownership enforcement.

Deliberately free of LLM dependencies so it can be unit tested in isolation.
The ownership check is the single most important guard in the pipeline: it is
what makes parallel coding safe.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Iterable

from .state import UnitContract


class ContractError(ValueError):
    """Raised when the Architect emits a contract the graph cannot execute."""


def _normalise(path: str) -> str:
    """Repo-relative, forward slashes, lower case (Windows-friendly compare)."""
    cleaned = path.replace("\\", "/").strip().strip("/")
    return str(Path(cleaned)).lower()


def load_contract(path: str | Path) -> list[UnitContract]:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    units: Iterable[dict[str, Any]] = data.get("units", data) if isinstance(data, dict) else data
    units = list(units)
    validate_units(units)
    return units  # type: ignore[return-value]


def validate_units(units: list[dict[str, Any]]) -> None:
    if not units:
        raise ContractError("contract contains no units")

    seen_ids: set[str] = set()
    owner: dict[str, str] = {}

    for unit in units:
        uid = unit.get("id") or "<unnamed>"
        for field in ("id", "instructions"):
            if not unit.get(field):
                raise ContractError(f"unit {uid} is missing required field '{field}'")

        if uid in seen_ids:
            raise ContractError(f"duplicate unit id: {uid}")
        seen_ids.add(uid)

        owns = unit.get("owns") or []
        if not owns:
            raise ContractError(f"unit {uid} declares no owned paths")

        for pattern in owns:
            key = _normalise(pattern)
            existing = owner.get(key)
            if existing and existing != uid:
                raise ContractError(
                    f"ownership collision on '{key}': claimed by both '{existing}' and '{uid}'. "
                    "Repartition in the Architect before spending tokens."
                )
            owner[key] = uid


def assert_owned(unit: UnitContract, path: str) -> None:
    """Hard-fail if a coder wrote outside its declared ownership."""
    target = _normalise(path)
    for pattern in unit.get("owns", []):
        candidate = _normalise(pattern)
        if target == candidate or fnmatch.fnmatch(target, candidate):
            return
    raise ContractError(
        f"unit '{unit['id']}' attempted to write '{path}', which it does not own. "
        "Reject the patch rather than merging it."
    )


def owned_unit_for(units: list[UnitContract], path: str) -> UnitContract | None:
    for unit in units:
        try:
            assert_owned(unit, path)
        except ContractError:
            continue
        return unit
    return None
