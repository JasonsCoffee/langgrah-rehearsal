"""Blocking Unity Operator transport with durable, request-bound callbacks."""

from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Literal, Protocol
from urllib.request import Request, urlopen

from ...core.contracts import _object, _text, _strings, _items
from ...core.evidence import CompileResult, TestResult, Violation
from ...core.ownership import confined_path
from ...core.storage import atomic_write, file_guard
from ...core.verification import VerificationRequest, WorkerEvidence


class HTTP(Protocol):
    def __call__(self, port: int, method: str, path: str, body: dict[str, object] | None,
                 timeout: float) -> dict[str, object]: ...


def local_http(port: int, method: str, path: str, body: dict[str, object] | None,
               timeout: float) -> dict[str, object]:
    payload = None if body is None else json.dumps(body).encode()
    request = Request(f"http://127.0.0.1:{port}{path}", data=payload, method=method,
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return _object(json.loads(response.read()))


def _command_error(response: dict[str, object]) -> str | None:
    if response.get("status") == "error":
        return str(response.get("message", "Bridge command error"))
    for key in ("result", "data"):
        nested = response.get(key)
        if isinstance(nested, str) and nested.startswith("{"):
            nested = json.loads(nested)
        if isinstance(nested, dict):
            error = _command_error(_object(nested))
            if error:
                return error
    return None


class _DiscoveryReload(ValueError):
    pass


class BridgeTransport:
    def __init__(self, root: Path, *, ports: tuple[int, ...], http: HTTP = local_http,
                 clock: Callable[[], float] = time.monotonic, pause: Callable[[float], None] = time.sleep,
                 timeout: float = 180, poll_interval: float = .5) -> None:
        if not ports or len(ports) > 16 or len(set(ports)) != len(ports) or any(not 1 <= p <= 65535 for p in ports):
            raise ValueError("Bridge discovery needs 1-16 distinct configured ports")
        if timeout <= 0 or not 0 < poll_interval <= min(5, timeout):
            raise ValueError("Invalid bounded worker timing")
        self.root, self.ports, self.http = root.resolve(), ports, http
        self.clock, self.pause, self.timeout, self.interval = clock, pause, timeout, poll_interval
        self._known_ports: set[int] = set()

    def _discover(self) -> int:
        deadline = self.clock() + self.timeout
        while True:
            try:
                return self._discover_once()
            except _DiscoveryReload:
                if self.clock() >= deadline:
                    raise ValueError("Verified-project discovery did not recover before deadline") from None
                self.pause(min(self.interval, deadline - self.clock()))

    def _discover_once(self) -> int:
        transient = False
        for port in self.ports:
            try:
                health = self.http(port, "GET", "/", None, min(1, self.timeout))
                if health.get("status") != "ok" or Path(_text(health.get("projectPath"))).resolve() != self.root:
                    continue
                self._known_ports.add(port)
                if "FrameworkVerify" in health.get("commands", ()):
                    return port
                # The installed Bridge queries scene state on its HTTP thread;
                # that can abort health command enumeration. Verify main-thread
                # availability, then query our side-effect-free protocol command.
                info = self.http(port, "GET", "/resource/project_info", None, min(5, self.timeout))
                if info.get("status") != "success" or not _object(json.loads(_text(info.get("data")))).get("unityVersion"):
                    continue
                self._check_project(port)
                response = self.http(port, "POST", "/execute", {"command": "FrameworkVerifyCapabilities"}, min(5, self.timeout))
                if response.get("status") != "success" or _command_error(response):
                    continue
                capability = _object(json.loads(_text(response.get("data"))))
                if (capability.get("protocol") == 1 and capability.get("command") == "FrameworkVerify"
                    and capability.get("modes") == ["compile", "tests"]):
                    return port
            except OSError:
                transient = transient or port in self._known_ports
                continue
            except (ValueError, TypeError):
                continue
        if transient:
            raise _DiscoveryReload("Verified project is reloading")
        raise ValueError("No exact-project Bridge with FrameworkVerify tooling")

    def _check_project(self, port: int) -> None:
        health = self.http(port, "GET", "/", None, min(1, self.timeout))
        if health.get("status") != "ok" or Path(_text(health.get("projectPath"))).resolve() != self.root:
            raise ValueError("Bridge project identity changed")

    def _execute(self, request: VerificationRequest, mode: Literal["compile", "tests"]) -> dict[str, object]:
        wire = json.loads(json.dumps(asdict(request)))
        envelope = {"request": wire, "mode": mode}
        raw = json.dumps(envelope, sort_keys=True).encode()
        ticket = sha256(raw).hexdigest()
        prefix = f".agent/verification/{ticket}"
        # Single worker across modes and requests. No retry can submit an intent
        # twice; ambiguous submission/reload must reconcile durable callbacks.
        with file_guard(self.root, ".agent/verification.guard"):
            port = self._discover()
            intent = confined_path(self.root, prefix + "/request.json")
            result_path = confined_path(self.root, prefix + "/result.json")
            task_id: str | None = None
            if not intent.exists():
                atomic_write(self.root, prefix + "/request.json", raw)
                try:
                    response = self.http(port, "POST", "/execute", {"command": "FrameworkVerify", "ticket": ticket}, min(5, self.timeout))
                except OSError:
                    # Submission may already have executed. Retain the durable
                    # intent and await callbacks; never submit it again.
                    response = {}
                error = _command_error(response)
                if error:
                    raise ValueError(error)
                if "taskId" in response:
                    task_id = _text(response["taskId"])
                    if not all(c.isalnum() or c in "-_" for c in task_id):
                        raise ValueError("Invalid Bridge task identity")
            elif intent.read_bytes() != raw:
                raise ValueError("Durable request identity mismatch")
            deadline = self.clock() + self.timeout
            while True:
                try:
                    self._check_project(port)
                except OSError:
                    if self.clock() >= deadline:
                        raise ValueError("Bridge did not recover before verification deadline")
                    self.pause(min(self.interval, deadline - self.clock()))
                    continue
                if result_path.exists():
                    result = _object(json.loads(result_path.read_bytes()))
                    if result.get("request") != wire or result.get("mode") != mode:
                        raise ValueError("Stale callback request/candidate provenance")
                    if result.get("status") != "completed":
                        raise ValueError(str(result.get("message", "Callback did not complete")))
                    return result
                if task_id:
                    try:
                        response = self.http(port, "GET", "/task/" + task_id, None, min(1, self.timeout))
                    except OSError:
                        response = {}
                    error = _command_error(response)
                    if error and "not found" not in error:
                        raise ValueError(error)
                    if error:
                        task_id = None
                if self.clock() >= deadline:
                    raise ValueError("Verification timed out; retain intent and reconcile before retry")
                self.pause(min(self.interval, deadline - self.clock()))

    def compile(self, request: VerificationRequest) -> WorkerEvidence:
        try:
            result = self._execute(request, "compile")
            passed = result.get("passed")
            if type(passed) is not bool:
                raise ValueError("Missing compilation result")
            violations = tuple(Violation(_text(v.get("code")), str(v.get("file", "")),
                                         str(v.get("symbol", "")), _text(v.get("message")))
                               for item in result.get("violations", []) for v in [_object(item)])
            if passed and violations:
                raise ValueError("Contradictory compilation result")
            return WorkerEvidence(request, compilation=CompileResult(passed, violations))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return WorkerEvidence(request, compilation=CompileResult(False, operational_error=str(exc)))

    def run_tests(self, request: VerificationRequest) -> WorkerEvidence:
        try:
            result = self._execute(request, "tests")
            groups = tuple(_strings(result.get(key)) for key in
                           ("discovered", "executed", "passed", "failed", "skipped", "inconclusive"))
            details = tuple(_object(item) for item in _items(result.get("failure_details", [])))
            names = tuple(_text(item.get("test")) for item in details)
            if len(set(names)) != len(names) or set(names) != set(groups[3]):
                raise ValueError("Failed tests require exact failure classification evidence")
            suite_errors = tuple(_text(item) for item in _items(result.get("suite_errors", [])))
            behavioral = not suite_errors
            messages = list(suite_errors)
            for item in details:
                state, site = _text(item.get("state")), _text(item.get("site"))
                behavioral = behavioral and state == "Failed" and site == "Test"
                messages.append(_text(item.get("test")) + ": " + _text(item.get("message")))
            return WorkerEvidence(request, tests=TestResult(*groups,
                failure_kind="assertion" if behavioral else "setup", messages=tuple(messages)))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return WorkerEvidence(request, tests=TestResult((), (), (), (), operational_error=str(exc)))
