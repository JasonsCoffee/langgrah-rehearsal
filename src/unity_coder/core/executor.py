"""Durable production stage driver with explicit trusted-host service injection."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol
from threading import Event, Thread
from contextlib import contextmanager
from collections.abc import Iterator

from .budget import BudgetLedger
from .contracts import Contract
from .journal import run_prefix
from .lifecycle import RunLease
from .ownership import confined_path
from .progress import ProgressStore
from .storage import atomic_write, file_guard


STAGES = ("prepare", "red", "code", "verify", "refactor", "final_verify", "review", "finalize", "repair", "rework")
TRANSITIONS = {"prepare": {"prepare", "red"}, "red": {"prepare", "code"}, "code": {"code", "verify"},
               "verify": {"code", "refactor"}, "refactor": {"final_verify"},
               "final_verify": {"code", "review"}, "review": set(), "finalize": set(), "repair":{"code"}, "rework":set()}


@dataclass(frozen=True)
class StepResult:
    next_stage: str
    units: Mapping[str, str]
    result: Mapping[str, object] | None = None


class ExecutionServices(Protocol):
    """Host-owned TDD, workers, verification, review and governors.

    Services journal effects and enforce the verification ladder. Pending steps
    are reconciled explicitly, never submitted again by this driver.
    """
    def step(self, stage: str, operation_id: str) -> StepResult: ...
    def reconcile(self, stage: str, operation_id: str) -> StepResult: ...


class ProductionExecutor:
    def __init__(self, root: Path, run_id: str, contract: Contract, budget: BudgetLedger,
                 lease: RunLease, services: ExecutionServices) -> None:
        self.root, self.run_id, self.contract = root, run_id, contract
        self.budget, self.lease, self.services = budget, lease, services
        self.prefix = run_prefix(run_id)
        self.path = self.prefix + f"/executor-v{contract.contract_version}.json"
        if (budget.root.resolve() != root.resolve() or budget.path != self.prefix + "/budget.json"
            or lease.root.resolve() != root.resolve() or lease.run_id != run_id):
            raise ValueError("Executor resources belong to another run")
        self.progress = ProgressStore(root, run_id, contract_version=contract.contract_version, contract_sha256=contract.sha256)

    def _read(self) -> dict:
        path = confined_path(self.root, self.path)
        if not path.exists():
            return {"format_version":1, "run_id":self.run_id, "contract_version":self.contract.contract_version,
                    "contract_sha256":self.contract.sha256, "stage":"prepare", "steps":[], "pending":None}
        state = json.loads(path.read_bytes())
        self._identity(state)
        return state

    def _identity(self, value: Mapping[str, object]) -> None:
        if (value.get("format_version") != 1 or value.get("run_id") != self.run_id
            or value.get("contract_version") != self.contract.contract_version
            or value.get("contract_sha256") != self.contract.sha256):
            raise ValueError("Executor contract identity mismatch")

    def _write(self, state: Mapping[str, object]) -> None:
        atomic_write(self.root, self.path, json.dumps(state, sort_keys=True).encode())

    def stage(self) -> str:
        self.lease.assert_held()
        return str(self._read()["stage"])

    def request_cancel(self) -> None:
        """Trusted host request; completion waits for active services to quiesce."""
        self.lease.assert_held()
        if self._read()["stage"] in ("finalize", "ended"):
            raise ValueError("Cannot cancel terminal or finalizing execution")
        atomic_write(self.root,self.prefix + "/cancel.json",json.dumps({
            "requested":True,"contract_sha256":self.contract.sha256}).encode())

    @contextmanager
    def _observe(self, stage: str) -> Iterator[None]:
        stopped = Event()
        errors: list[Exception] = []
        def publish() -> None:
            snapshot = getattr(self.services,"progress_snapshot",lambda: ({}, {}, None))()
            used = self.budget.totals()
            self.progress.publish(stage,units=snapshot[0],attempts=snapshot[1],active_verification=snapshot[2],
                                  budget={"input_tokens":used[0],"output_tokens":used[1]})
        def heartbeat() -> None:
            while not stopped.wait(.25):
                try: publish()
                except Exception as error:
                    errors.append(error)
                    return
        publish()
        thread = Thread(target=heartbeat,name="execution-heartbeat",daemon=True)
        thread.start()
        try:
            yield
            if errors: raise errors[0]
        finally:
            stopped.set()
            thread.join()

    def _validate_terminal(self, result: Mapping[str, object], stage: str) -> None:
        self._identity(result)
        path = confined_path(self.root, self.prefix + "/result.json")
        if not path.exists() or json.loads(path.read_bytes()) != dict(result):
            raise ValueError("Stage result requires its durable receipt")
        outcome = result.get("outcome")
        if outcome not in ("operational", "cancelled", "rework", "abandon", "awaiting_human_review", "pass"):
            raise ValueError("Unknown executor outcome")
        if outcome == "awaiting_human_review" and stage != "review":
            raise ValueError("Review cannot bypass final verification")
        if outcome == "pass":
            if stage != "finalize":
                raise ValueError("Accepted pass requires finalization")
            review = json.loads(confined_path(self.root, self.prefix + "/review.json").read_bytes())
            request = review.get("request", {})
            if (review.get("decision") != "accept" or not review.get("reviewer")
                or review.get("reviewer") != result.get("reviewer")
                or request.get("candidate_revision") != result.get("approved_parent")
                or request.get("contract_sha256") != self.contract.sha256
                or request.get("run_id") != self.run_id):
                raise ValueError("Finalization lacks matching human acceptance")

    def advance(self, expected_stage: str) -> StepResult:
        self.lease.assert_held()
        with file_guard(self.root, self.prefix + "/executor.guard"):
            state = self._read()
            stage = str(state["stage"])
            if stage != expected_stage or stage not in STAGES:
                raise ValueError("Stale executor stage")
            if state.get("retire_result") is not None:
                previous = state["retire_result"]
                archive = self.prefix + f"/resumed-results/step{len(state['steps'])}.json"
                atomic_write(self.root,archive,json.dumps(previous,sort_keys=True).encode())
                active = confined_path(self.root,self.prefix + "/result.json")
                if active.exists():
                    if json.loads(active.read_bytes()) != previous:
                        raise ValueError("Result changed during explicit resume")
                    active.unlink()
                state.pop("retire_result")
                self._write(state)
            self.budget.begin_cycle(self.contract.contract_version, self.contract.sha256,
                                   {u.id:self.contract.lineage_for(u.id) for u in self.contract.units})
            operation = f"v{self.contract.contract_version}-step{len(state['steps']) + 1}-{stage}"
            if state["pending"] is None:
                state["pending"] = operation
                self._write(state)
                with self._observe(stage):
                    report = self.services.step(stage, operation)
            else:
                if state["pending"] != operation:
                    raise ValueError("Pending step identity changed")
                with self._observe(stage):
                    report = self.services.reconcile(stage, operation)
            if report.next_stage == "ended":
                if report.result is None:
                    raise ValueError("Ended stage requires structured outcome")
                self._validate_terminal(report.result, stage)
            elif report.next_stage not in TRANSITIONS[stage] or report.result is not None:
                raise ValueError("Illegal executor stage transition")
            steps = list(state["steps"])
            steps.append({"operation_id":operation, "stage":stage, "next_stage":report.next_stage,
                          "units":dict(report.units), "result":dict(report.result) if report.result else None})
            state.update(stage=report.next_stage, steps=steps, pending=None)
            self._write(state)
            used = self.budget.totals()
            snapshot = getattr(self.services,"progress_snapshot",lambda: ({}, {}, None))()
            self.progress.publish(report.next_stage, units=report.units,
                                  attempts=snapshot[1],
                                  budget={"input_tokens":used[0],"output_tokens":used[1]})
            return report

    def outcome(self) -> str | None:
        state = self._read()
        if state["stage"] != "ended":
            return None
        last = state["steps"][-1]
        self._validate_terminal(last["result"], last["stage"])
        return str(last["result"]["outcome"])

    def resume_review(self) -> None:
        """Consume an already authenticated review, never accept model approval."""
        self.lease.assert_held()
        with file_guard(self.root,self.prefix + "/executor.guard"):
            state = self._read()
            if state["stage"] != "ended" or self.outcome() != "awaiting_human_review":
                raise ValueError("Only a waiting reviewed invocation can resume")
            record = json.loads(confined_path(self.root,self.prefix + "/review.json").read_bytes())
            request = record.get("request",{})
            result = state["steps"][-1]["result"]
            if (request.get("run_id") != self.run_id or request.get("contract_version") != self.contract.contract_version
                or request.get("contract_sha256") != self.contract.sha256
                or request.get("candidate_revision") != result.get("candidate_revision")
                or not record.get("reviewer")):
                raise ValueError("Review identity is stale or unauthenticated")
            next_stage = {"accept":"finalize","implementation":"repair","contract":"rework"}.get(record.get("decision"))
            if next_stage is None:
                raise ValueError("Pending review cannot resume execution")
            state.update(stage=next_stage,pending=None,retire_result=result)
            self._write(state)

    def resume_operational(self, *, reconcile: Callable[[], bool]) -> None:
        """Explicit host recovery, retaining paid usage and completed stage history."""
        self.lease.assert_held()
        with file_guard(self.root,self.prefix + "/executor.guard"):
            state = self._read()
            if state["stage"] != "ended" or self.outcome() != "operational":
                raise ValueError("Invocation is not an operational stop")
            if not reconcile():
                raise ValueError("Operational effects and provider usage must be reconciled")
            state.update(stage=state["steps"][-1]["stage"],pending=None,retire_result=state["steps"][-1]["result"])
            self._write(state)
