"""Leased, recoverable same-run contract transitions; accounting is never reset."""

from collections.abc import Callable
import json
from pathlib import Path

from .architect_boundary import PlanningContext
from .budget import BudgetLedger
from .contracts import Contract
from .journal import run_prefix
from .lifecycle import RunLease
from .ownership import confined_path
from .progress import ProgressStore
from .storage import atomic_write, file_guard


def transition_cycle(planning_root: Path, state_root: Path, run_id: str,
                     previous: Contract, current: Contract, context: PlanningContext,
                     budget: BudgetLedger, lease: RunLease, *,
                     workers_reconciled: Callable[[], bool]) -> None:
    """Both contracts must have passed the consecutive-revision contract loader.

    Persist complete transition intent before touching accounting or active files.
    Recovery accepts only the recorded old bytes or the intended new state. Model
    calls, operation journals, dossiers and cycle branches remain in place.
    """
    prefix = run_prefix(run_id)
    if (lease.root.resolve() != state_root.resolve() or lease.run_id != run_id
        or budget.root.resolve() != state_root.resolve() or budget.path != prefix + "/budget.json"):
        raise ValueError("Transition lease/budget belongs to another run")
    lease.assert_held()
    if current.contract_version != previous.contract_version + 1:
        raise ValueError("Contract transition must be consecutive")
    context.validate(planning_root)
    known = {task.task_ref for task in context.tasks}
    if any(link.task_ref not in known for link in current.task_links):
        raise ValueError("Unknown next-cycle task")
    if not workers_reconciled():
        raise ValueError("Workers must be reconciled before cycle transition")
    identity = {"format_version": 1, "run_id": run_id, "contract_version": current.contract_version,
                "contract_sha256": current.sha256, "context": context.to_dict()}
    intent_path = prefix + f"/transitions/v{current.contract_version}.json"
    with file_guard(state_root, prefix + "/boundary.guard"):
        path = confined_path(state_root, intent_path)
        if path.exists():
            intent = json.loads(path.read_bytes())
            if intent["next"] != identity or intent["previous_sha256"] != previous.sha256:
                raise ValueError("Transition intent identity changed")
            if intent["state"] == "complete":
                if json.loads(confined_path(state_root, prefix + "/invocation.json").read_bytes()) != identity:
                    raise ValueError("Completed transition is no longer current")
                return
        else:
            invocation = json.loads(confined_path(state_root, prefix + "/invocation.json").read_bytes())
            result = json.loads(confined_path(state_root, prefix + "/result.json").read_bytes())
            dossier_path = confined_path(state_root, prefix + f"/dossier-v{previous.contract_version}.json")
            if not dossier_path.exists():
                raise ValueError("Contract rework requires its dossier")
            dossier = json.loads(dossier_path.read_bytes())
            for record in (invocation, result, dossier):
                if (record.get("run_id") != run_id or record.get("contract_version") != previous.contract_version
                    or record.get("contract_sha256") != previous.sha256):
                    raise ValueError("Previous cycle identity mismatch")
            if result.get("outcome") != "rework" or dossier.get("reason") != "rework":
                raise ValueError("Only completed contract rework can advance")
            saved = {}
            for name in ("invocation.json", "result.json", "review.json", "status.json", "progress.jsonl"):
                source = confined_path(state_root, prefix + "/" + name)
                if source.exists():
                    saved[name] = source.read_bytes().hex()
            intent = {"state": "pending", "previous_sha256": previous.sha256, "next": identity, "saved": saved}
            atomic_write(state_root, intent_path, json.dumps(intent, sort_keys=True).encode())
        budget.begin_cycle(current.contract_version, current.sha256,
                           {u.id: current.lineage_for(u.id) for u in current.units})
        for name, content in intent["saved"].items():
            archive = prefix + f"/cycles/v{previous.contract_version}/" + name
            target = confined_path(state_root, archive)
            raw = bytes.fromhex(content)
            if target.exists() and target.read_bytes() != raw:
                raise ValueError("Archived cycle bytes changed")
            atomic_write(state_root, archive, raw)
        for name in ("result.json", "review.json"):
            target = confined_path(state_root, prefix + "/" + name)
            if target.exists():
                if name not in intent["saved"] or target.read_bytes().hex() != intent["saved"][name]:
                    raise ValueError("Active cycle result changed during transition")
                target.unlink()
        ProgressStore(state_root, run_id, contract_version=current.contract_version,
                      contract_sha256=current.sha256).transition(previous.contract_version, previous.sha256)
        active = confined_path(state_root, prefix + "/invocation.json").read_bytes()
        if active.hex() != intent["saved"]["invocation.json"] and json.loads(active) != identity:
            raise ValueError("Active invocation changed during transition")
        atomic_write(state_root, prefix + "/invocation.json", json.dumps(identity, sort_keys=True).encode())
        intent["state"] = "complete"
        atomic_write(state_root, intent_path, json.dumps(intent, sort_keys=True).encode())
