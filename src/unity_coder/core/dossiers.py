"""Portable backward-boundary records; no dossier-level defect classification."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Mapping

from .contracts import Contract
from .ownership import confined_path, portable_path
from .storage import atomic_write


@dataclass(frozen=True)
class DossierUnit:
    id: str
    defect_class: str
    criterion: str
    gate: str
    evidence_refs: tuple[str, ...]
    hypothesis: str
    attempts: int
    history: tuple[str, ...]


def emit_dossier(root: Path, run_id: str, contract: Contract, units: tuple[DossierUnit, ...], *,
                  budget_remaining: Mapping[str, int], reason: str = "rework") -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id) or reason not in ("rework", "budget"):
        raise ValueError("Invalid run ID or dossier reason")
    if reason == "rework" and not any(u.defect_class == "contract" for u in units):
        raise ValueError("Implementation-only failure remains inside execution")
    active = {u.id for u in contract.units if u.status == "active"}
    if len({u.id for u in units}) != len(units):
        raise ValueError("Duplicate unit dossier entry")
    for unit in units:
        if unit.id not in active or unit.defect_class not in ("implementation", "contract"):
            raise ValueError("Invalid per-unit classification")
        if unit.gate not in ("ownership", "conformance", "compile", "tests") or unit.attempts < 0:
            raise ValueError("Invalid gate or attempt count")
        if not unit.criterion or not unit.evidence_refs:
            raise ValueError("Dossier needs criterion and evidence provenance")
        for ref in unit.evidence_refs:
            portable_path(ref)
    if any(type(n) is not int or n < 0 for n in budget_remaining.values()):
        raise ValueError("Invalid remaining budget")
    payload = {"dossier_version": 1, "run_id": run_id,
               "contract_version": contract.contract_version,
               "contract_sha": contract.sha256, "contract_sha256": contract.sha256,
               "verdict": "fail", "reason": reason,
               "failed_units": [asdict(u) for u in units],
               "budget_remaining": dict(budget_remaining)}
    content = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    relative = Path(f".agent/runs/{run_id}/dossier-v{contract.contract_version}.json")
    target = confined_path(root, relative.as_posix())
    if target.exists() and target.read_bytes() != content:
        raise ValueError("Dossier identity already exists with different evidence")
    atomic_write(root, relative.as_posix(), content)
    return relative
