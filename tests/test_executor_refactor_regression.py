"""Frozen production rollback of a behavioral Refactor regression."""

from test_local_executor import local, run
from test_workspaces import workspace
from test_contracts import bundle
from unity_coder.core.local_executor import WorkerPatch


def test_refactor_failure_restores_green_before_the_bounded_retry(local):
    executor,services,workers,_,_,_=local
    original=workers.code
    refactored=set()
    retries=[]
    def code(unit,stage,files,feedback,operation):
        if stage=="refactor" and unit.id not in refactored:
            refactored.add(unit.id)
            return WorkerPatch({p:b"regressed" for p in unit.owns},"Broken refactor fixture")
        if stage=="green" and feedback:
            retries.append(all(files[p]=="implemented" for p in unit.owns))
        return original(unit,stage,files,feedback,operation)
    workers.code=code
    assert run(executor)["outcome"]=="awaiting_human_review"
    assert retries==[True,True]
    assert services.retry.state("U1-state").regressions==1
