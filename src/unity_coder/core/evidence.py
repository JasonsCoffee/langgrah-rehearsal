"""Stack-neutral immutable evidence exchanged by adapters and gates."""

from dataclasses import dataclass
from typing import Literal

Gate = Literal["ownership", "conformance", "compile", "tests"]


@dataclass(frozen=True)
class Violation:
    code: str
    file: str
    symbol: str
    message: str


@dataclass(frozen=True)
class CompileResult:
    passed: bool
    violations: tuple[Violation, ...] = ()
    operational_error: str | None = None


@dataclass(frozen=True)
class TestResult:
    discovered: tuple[str, ...]
    executed: tuple[str, ...]
    passed: tuple[str, ...]
    failed: tuple[str, ...]
    skipped: tuple[str, ...] = ()
    inconclusive: tuple[str, ...] = ()
    operational_error: str | None = None
    failure_kind: str = "assertion"
    messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class CostProfile:
    compile_seconds: float
    test_seconds: float
