"""Frozen bounded test-author preparation before the global freeze."""

from test_local_executor import local, run
from test_workspaces import workspace
from test_contracts import bundle
from unity_coder.core.local_executor import TestReviewRejected, WorkerPatch


def test_invalid_tests_are_reauthored_with_bounded_attempts_before_impl(local):
    executor,services,workers,verified,_,_=local
    reviews=[]
    coding=[]
    def reject(unit,files,operation):
        reviews.append(operation)
        raise TestReviewRejected("Missing behavioral assertion")
    def author(unit,stage,files,feedback,operation):
        coding.append(stage)
        return WorkerPatch({p:b"revised test" for p in unit.owns},"Repair test coverage")
    workers.review_tests=reject
    workers.code=author
    assert run(executor)["outcome"]=="rework"
    assert len(reviews)==3
    assert coding==["test_authoring","test_authoring"]
    assert verified==[]
    assert not services.tdd.frozen
    assert services.tdd.state("U0-tests").preparation_attempts==3
