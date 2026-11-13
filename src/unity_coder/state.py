"""Graph state for the Unity coding pipeline.

All fields are optional (``total=False``) so every node can return a partial
update. Fields annotated with a reducer accumulate instead of overwriting.
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class UnitContract(TypedDict):
    """One coding unit emitted by the Architect.

    ``owns`` is the safety mechanism: a coder may only write paths matching
    this list, and no two units may claim the same path.
    """

    id: str
    title: str
    spec_ref: str
    owns: list[str]
    instructions: str
    acceptance: list[str]


class FilePatch(TypedDict):
    path: str
    content: str
    action: Literal["create", "update"]


class UnitResult(TypedDict):
    unit_id: str
    cycle: int
    ok: bool
    notes: str
    patches: list[FilePatch]


class VerifyResult(TypedDict):
    compiled: bool
    compile_errors: list[str]
    tests_total: int
    tests_failed: int
    failing_tests: list[str]
    duration_s: float


class UnitPayload(TypedDict):
    """Payload delivered to a single coder via ``Send``.

    ``Send`` replaces the node input, so the payload must be self-contained.
    """

    unit: UnitContract
    project_root: str
    cycle: int
    conventions: str


class WorkflowState(TypedDict, total=False):
    # inputs
    contract_path: str
    project_root: str
    unity_exe: str
    max_cycles: int
    commit: bool

    # derived
    units: list[UnitContract]
    cycle: int
    results: Annotated[list[UnitResult], operator.add]
    verify: VerifyResult
    dossier: dict
    phase: str
    log: Annotated[list[str], operator.add]
