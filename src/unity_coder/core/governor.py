"""Budget stop, worker reconciliation, retained branches and abandon dossier."""
from collections.abc import Callable
import json
from .branches import CycleBranches
from .budget import BudgetLedger
from .dossiers import DossierUnit, emit_dossier
from .lifecycle import RunLifecycle
from .ownership import confined_path
from .storage import file_guard
from .workspaces import Workspace, WorkspaceManager


class BudgetGovernor:
    def __init__(self, manager: WorkspaceManager, integration: Workspace, budget: BudgetLedger) -> None:
        self.manager,self.integration,self.budget=manager,integration,budget
        self.lifecycle=RunLifecycle(budget.root,manager.run_id,
            contract_version=manager.contract.contract_version,contract_sha256=manager.contract.sha256)
        if budget.path!=self.lifecycle.prefix+'/budget.json':
            raise ValueError('Governor and budget must belong to the same run')
        self.branches=CycleBranches(manager,budget.root)

    def abandon(self, *, reconcile_workers: Callable[[], bool],
                input_tokens: int = 0, output_tokens: int = 0, cycle_exhausted: bool = False,
                units: tuple[DossierUnit, ...] = ()) -> dict[str, object]:
        """Stop paid dispatch before asking the trusted host to quiesce workers.

        A false reconciliation result retains the current candidate and requires
        another reconciliation attempt; it never kills or resets a live worker.
        """
        with file_guard(self.budget.root,self.lifecycle.prefix+'/governor.guard'):
            used=self.budget.stop_for_budget(input_tokens=input_tokens,output_tokens=output_tokens,cycle_exhausted=cycle_exhausted)
            if not reconcile_workers():
                raise ValueError('Budget stopped; active workers must be reconciled before abandonment')
            result_path=confined_path(self.budget.root,self.lifecycle.prefix+'/result.json')
            if result_path.exists():
                prior=json.loads(result_path.read_bytes())
                if prior['outcome']!='abandon' or prior['reason']!='budget':
                    raise ValueError('Run already has a conflicting terminal outcome')
                self.branches.abandon(self.integration)
                return prior
            branch=self.branches.abandon(self.integration)
            evidence=emit_dossier(self.budget.root,self.manager.run_id,self.manager.contract,units,
                budget_remaining={'input_tokens':max(0,self.budget.limits[0]-used[0]),
                                  'output_tokens':max(0,self.budget.limits[1]-used[1])},reason='budget')
            return self.lifecycle.finish('abandon',candidate_revision=branch['candidate_revision'],
                reason='budget',evidence_refs=(evidence.as_posix(),))
