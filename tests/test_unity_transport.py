"""Frozen Bridge protocol tests; injected HTTP and clock never use a network."""

from dataclasses import asdict, replace
import json

import pytest

from unity_coder.adapters.unity.transport import BridgeTransport
from unity_coder.core.verification import VerificationRequest


class FakeBridge:
    def __init__(self, root):
        self.root = root
        self.project = str(root)
        self.commands = ["FrameworkVerify"]
        self.calls = []
        self.ticks = 0.0
        self.submission = {"status": "running", "taskId": "t1"}
        self.task = {"status": "success"}
        self.on_wait = lambda: None
    def http(self, port, method, path, body, timeout):
        self.calls.append((port, method, path, body))
        if path == "/":
            return {"status": "ok", "projectPath": self.project, "commands": self.commands}
        if path == "/execute": return self.submission
        return self.task
    def clock(self): return self.ticks
    def wait(self, seconds):
        self.ticks += seconds
        self.on_wait()


@pytest.fixture
def bridge(tmp_path):
    fake = FakeBridge(tmp_path)
    def worker():
        return BridgeTransport(tmp_path, ports=(59183, 59184), http=fake.http,
                               clock=fake.clock, pause=fake.wait, timeout=2, poll_interval=.5)
    req = VerificationRequest("req1", "run1", 1, "contract", "candidate", "presentation", "profile", "env", ("Test",), True)
    return fake, worker, req


def publish(fake, request, *, mode="tests", alter=None):
    wire = json.loads(json.dumps(asdict(request)))
    if alter: wire.update(alter)
    payload = {"request": wire, "mode": mode, "status": "completed"}
    if mode == "compile": payload.update(passed=True, violations=[])
    else: payload.update(discovered=["Test"], executed=["Test"], passed=["Test"], failed=[], skipped=[], inconclusive=[])
    for intent in fake.root.glob(".agent/verification/*/request.json"):
        (intent.parent / "result.json").write_text(json.dumps(payload))


def test_command_success_is_not_test_completion(bridge):
    fake, factory, req = bridge
    result = factory().run_tests(req)
    assert result.tests.operational_error
    assert fake.ticks >= 2
    assert sum(call[2] == "/execute" for call in fake.calls) == 1


def test_callback_result_is_normalized_and_bound_to_request(bridge):
    fake, factory, req = bridge
    fake.on_wait = lambda: publish(fake, req)
    result = factory().run_tests(req)
    assert result.request == req
    assert result.tests.passed == ("Test",) and result.tests.operational_error is None


def test_compile_requires_its_own_durable_result(bridge):
    fake, factory, req = bridge
    fake.on_wait = lambda: publish(fake, req, mode="compile")
    assert factory().compile(req).compilation.passed


@pytest.mark.parametrize("field", ["candidate_revision", "contract_sha256", "presentation_sha256", "request_id"])
def test_stale_provenance_is_operational(bridge, field):
    fake, factory, req = bridge
    fake.on_wait = lambda: publish(fake, req, alter={field: "stale"})
    assert factory().run_tests(req).tests.operational_error


def test_wrong_project_is_never_sent_commands(bridge):
    fake, factory, req = bridge
    fake.project = str(fake.root / "another")
    assert factory().run_tests(req).tests.operational_error
    assert all(call[2] == "/" for call in fake.calls)
    assert len(fake.calls) == 2


def test_missing_tooling_is_operational_without_installation(bridge):
    fake, factory, req = bridge
    fake.commands = []
    assert factory().compile(req).compilation.operational_error
    assert all(call[1] == "GET" for call in fake.calls)


def test_nested_command_error_is_not_success(bridge):
    fake, factory, req = bridge
    fake.submission = {"status": "success", "result": {"status": "error", "message": "bad command"}}
    assert factory().run_tests(req).tests.operational_error


def test_reload_loses_task_id_but_durable_callback_still_completes(bridge):
    fake, factory, req = bridge
    fake.task = {"status": "error", "message": "Task 't1' not found"}
    fake.on_wait = lambda: publish(fake, req)
    assert factory().run_tests(req).tests.passed == ("Test",)


def test_restart_after_timeout_never_duplicates_submission(bridge):
    fake, factory, req = bridge
    assert factory().run_tests(req).tests.operational_error
    publish(fake, req)
    assert factory().run_tests(req).tests.passed == ("Test",)
    assert sum(call[2] == "/execute" for call in fake.calls) == 1


def test_malformed_result_is_operational(bridge):
    fake, factory, req = bridge
    def partial():
        for intent in fake.root.glob(".agent/verification/*/request.json"):
            (intent.parent / "result.json").write_text('{"request":')
    fake.on_wait = partial
    assert factory().run_tests(req).tests.operational_error


def test_discovery_is_bounded(bridge):
    fake, _, _ = bridge
    with pytest.raises(ValueError):
        BridgeTransport(fake.root, ports=tuple(range(59000, 59100)), http=fake.http)
