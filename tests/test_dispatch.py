"""Frozen dispatch checks use fake agents and local synchronization only."""

from threading import Barrier

from test_tdd import coordinator, prepare
from test_contracts import bundle
from unity_coder.core.dispatch import dispatch_parallel, ready_units


def test_only_test_authors_ready_before_freeze(coordinator):
    assert ready_units(coordinator) == ("U0-tests",)


def test_frozen_interface_allows_parallel_dependents(coordinator):
    prepare(coordinator)
    assert set(ready_units(coordinator)) == {"U1-state", "U2-system"}


def test_fake_agents_overlap_after_freeze(coordinator):
    prepare(coordinator)
    rendezvous = Barrier(2)
    def agent(unit):
        rendezvous.wait(timeout=5)
        return {unit.owns[0]: b"implementation"}
    results = dispatch_parallel(coordinator, agent)
    assert {r.unit_id for r in results} == {"U1-state", "U2-system"}
    assert all(r.base_revision == "base" for r in results)


def test_dispatch_validates_owned_output(coordinator):
    prepare(coordinator)
    def agent(unit):
        return {"Tests/Runtime/Script/QueueReorderTests.cs": b"weakened"}
    results = dispatch_parallel(coordinator, agent)
    assert results
    assert all(r.violation and not r.changes for r in results)
