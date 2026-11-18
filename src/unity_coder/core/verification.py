"""Blocking, serialized, stop-first verification of identified candidate inputs."""

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from types import MappingProxyType
from typing import Literal, Mapping, Protocol

from .adapters import StackAdapter
from .contracts import Contract
from .evidence import CompileResult, Gate, TestResult, Violation
from .ownership import validate_owned_path, within
from .tdd import BehaviorEvidence, validate_behavior


@dataclass(frozen=True)
class VerificationRequest:
    request_id: str
    run_id: str
    contract_version: int
    contract_sha256: str
    candidate_revision: str
    presentation_sha256: str
    coding_profile_sha256: str
    environment_sha256: str
    test_selection: tuple[str, ...]
    full_suite: bool = False


@dataclass(frozen=True)
class WorkerEvidence:
    request: VerificationRequest
    compilation: CompileResult | None = None
    tests: TestResult | None = None


class VerifyTransport(Protocol):
    def compile(self, request: VerificationRequest) -> WorkerEvidence: ...
    def run_tests(self, request: VerificationRequest) -> WorkerEvidence: ...


@dataclass(frozen=True)
class VerificationResult:
    request: VerificationRequest
    gate: Gate
    status: Literal["passed", "failed", "operational"]
    related_units: tuple[str, ...] = ()
    violations: tuple[Violation, ...] = ()
    failed_tests: tuple[str, ...] = ()
    test_result: TestResult | None = None
    full_suite_verified: bool = False
    behavioral: bool = False


class VerificationLadder:
    def __init__(self, adapter: StackAdapter, transport: VerifyTransport) -> None:
        self.adapter, self.transport = adapter, transport
        self._lock = Lock()

    def verify(self, request: VerificationRequest, contract: Contract, root: Path,
               patches: Mapping[str, Mapping[str, bytes | None]], files: Mapping[str, str | bytes], *,
               frozen_paths: tuple[str, ...] = ()) -> VerificationResult:
        """One ladder instance owns one worker; durable host leasing is separate.

        Copy inputs before acquiring the worker so later submissions cannot alter
        the candidate waiting for or undergoing verification.
        """
        frozen_patches = {u: dict(patch) for u, patch in patches.items()}
        candidate_files = dict(files)
        with self._lock:
            return self._verify(request, contract, root, frozen_patches,
                                candidate_files, frozen_paths)

    def _operational(self, request: VerificationRequest, gate: Gate, message: str) -> VerificationResult:
        return VerificationResult(request, gate, "operational", violations=(Violation("operational", "", "", message),))

    def _verify(self, request: VerificationRequest, contract: Contract, root: Path,
                patches: Mapping[str, Mapping[str, bytes | None]], files: dict[str, str | bytes],
                frozen_paths: tuple[str, ...]) -> VerificationResult:
        if (not request.request_id or not request.run_id or not request.candidate_revision
            or request.contract_version != contract.contract_version
            or request.contract_sha256 != contract.sha256
            or request.presentation_sha256 != contract.presentation_ref.sha256
            or request.coding_profile_sha256 != contract.coding_profile_ref.sha256
            or request.environment_sha256 != contract.environment_ref.sha256):
            return self._operational(request, "ownership", "Request identity does not match validated inputs")
        required = {t.test_id for t in contract.test_links}
        selected = set(request.test_selection)
        if (not selected or len(selected) != len(request.test_selection) or not selected <= required
            or (request.full_suite and selected != required)):
            return VerificationResult(request, "tests", "failed", violations=(Violation("test_evidence", "", "", "Invalid required test selection"),))
        units = {u.id: u for u in contract.units if u.status == "active"}
        protected = frozen_paths + (contract.spec.path, contract.presentation_ref.path,
                                    contract.coding_profile_ref.path, contract.environment_ref.path)
        for unit_id, patch in patches.items():
            try:
                if unit_id not in units:
                    raise ValueError("Patch belongs to no active unit")
                unit = units[unit_id]
                for path in patch:
                    validate_owned_path(path, (contract.module_root,) if unit.role == "impl" else contract.test_roots,
                                        root, self.adapter, protected)
                    if any(within(path, p, self.adapter) for p in frozen_paths):
                        raise ValueError("Patch modifies frozen content")
                    if not self.adapter.is_generated(path) and contract.owner_of(path) != unit_id:
                        raise ValueError("Patch modifies unowned content")
            except ValueError as exc:
                return VerificationResult(request, "ownership", "failed", (unit_id,),
                                          (Violation("ownership", "", "", str(exc)),))
        participants = tuple(sorted(patches))
        for patch in patches.values():
            for path, content in patch.items():
                if content is None:
                    files.pop(path, None)
                else:
                    files[path] = content
        snapshot = MappingProxyType(files)
        syntax = self.adapter.parse_check(snapshot)
        if syntax:
            return VerificationResult(request, "conformance", "failed", participants, syntax)
        interfaces = tuple(i for u in units.values() for i in u.interfaces)
        conformance = self.adapter.check_interfaces(snapshot, interfaces)
        if conformance:
            return VerificationResult(request, "conformance", "failed", participants, conformance)
        try:
            compile_evidence = self.transport.compile(request)
        except Exception as exc:
            return self._operational(request, "compile", f"Worker call failed: {type(exc).__name__}")
        if compile_evidence.request != request or compile_evidence.compilation is None:
            return self._operational(request, "compile", "Missing or stale compilation evidence")
        compilation = compile_evidence.compilation
        if compilation.operational_error:
            return self._operational(request, "compile", compilation.operational_error)
        if not compilation.passed or compilation.violations:
            return VerificationResult(request, "compile", "failed", participants, compilation.violations)
        try:
            test_evidence = self.transport.run_tests(request)
        except Exception as exc:
            return self._operational(request, "tests", f"Worker call failed: {type(exc).__name__}")
        if test_evidence.request != request or test_evidence.tests is None:
            return self._operational(request, "tests", "Missing or stale test evidence")
        tests = test_evidence.tests
        if tests.operational_error:
            return self._operational(request, "tests", tests.operational_error)
        try:
            validate_behavior(BehaviorEvidence(request.candidate_revision, request.test_selection, tests), request.test_selection)
        except ValueError as exc:
            return VerificationResult(request, "tests", "failed", violations=(Violation("test_evidence", "", "", str(exc)),),
                                      test_result=tests)
        if tests.failed:
            related = tuple(sorted({u for link in contract.test_links if link.test_id in tests.failed for u in link.implementing_units}))
            return VerificationResult(request, "tests", "failed", related, failed_tests=tests.failed,
                                      test_result=tests, behavioral=True)
        return VerificationResult(request, "tests", "passed", test_result=tests,
                                  full_suite_verified=request.full_suite, behavioral=True)
