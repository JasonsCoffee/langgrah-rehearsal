"""Additional TDD integrity regressions found during implementation review."""

import pytest

from test_contracts import bundle
from test_tdd import coordinator, evidence, prepare


def test_baseline_test_bytes_cannot_change_before_freeze(coordinator):
    c = coordinator
    c.approve_tests("U0-tests", "review")
    c.record_baseline("U1-state", evidence(c, "U1-state"))
    c.record_baseline("U2-system", evidence(c, "U2-system"))
    (c.root / "Tests/Runtime/Script/QueueReorderTests.cs").write_bytes(b"different tests")
    with pytest.raises(ValueError): c.freeze()


def test_refactor_failure_restores_only_owned_green_files(coordinator):
    c = coordinator
    prepare(c)
    own = c.root / "Runtime/Script/Queue/DinerState.cs"
    peer = c.root / "Runtime/Script/Queue/QueueSystem.cs"
    c.begin("U1-state")
    own.write_bytes(b"green")
    c.record_green("U1-state", evidence(c, "U1-state", failed=False, snapshot="green"))
    c.begin_refactor("U1-state")
    own.write_bytes(b"broken refactor")
    peer.write_bytes(b"peer work")
    c.finish_refactor("U1-state", evidence(c, "U1-state", snapshot="broken"))
    assert own.read_bytes() == b"green"
    assert peer.read_bytes() == b"peer work"


def test_changed_spec_invalidates_dispatch(coordinator):
    prepare(coordinator)
    (coordinator.root / coordinator.contract.spec.path).write_bytes(b"new spec")
    with pytest.raises(ValueError): coordinator.begin("U1-state")
