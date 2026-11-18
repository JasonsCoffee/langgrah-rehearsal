"""Immutable, hashed contracts validated before any execution effects."""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Literal, Mapping, cast

from .ownership import PathRules, confined_path, portable_path, validate_owned_path


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    sha256: str


@dataclass(frozen=True)
class Interface:
    symbol: str
    signature: str


@dataclass(frozen=True)
class Unit:
    id: str
    role: Literal["test", "impl"]
    status: Literal["active", "superseded"]
    title: str
    spec_ref: str
    owns: tuple[str, ...]
    acceptance: tuple[str, ...]
    depends_on: tuple[str, ...]
    interfaces: tuple[Interface, ...]
    instructions: str
    add_justification: str = ""


@dataclass(frozen=True)
class TestLink:
    test_id: str
    author_unit: str
    implementing_units: tuple[str, ...]
    criterion: str


@dataclass(frozen=True)
class TaskLink:
    task_ref: str
    unit_ids: tuple[str, ...]
    criteria: tuple[str, ...]


@dataclass(frozen=True)
class Migration:
    from_unit: str
    to_unit: str
    paths: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class Contract:
    format_version: int
    contract_version: int
    sha256: str
    module: str
    module_root: str
    test_roots: tuple[str, ...]
    spec: ArtifactRef
    presentation_ref: ArtifactRef
    coding_profile_ref: ArtifactRef
    environment_ref: ArtifactRef
    units: tuple[Unit, ...]
    test_links: tuple[TestLink, ...]
    task_links: tuple[TaskLink, ...]
    ownership_migrations: tuple[Migration, ...]
    _owners: Mapping[str, str] = field(repr=False)
    _lineages: Mapping[str, tuple[str, ...]] = field(repr=False)
    _rules: PathRules = field(repr=False, compare=False)

    def owner_of(self, path: str) -> str | None:
        return self._owners.get(self._rules.normalise_path(portable_path(path)))

    def lineage_for(self, unit_id: str) -> tuple[str, ...]:
        """Predecessors whose repair/resource history must remain attributable."""
        return self._lineages[unit_id]


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError("Expected JSON object")
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty string")
    return value


def _items(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Expected array")
    return value


def _strings(value: object, *, required: bool = False) -> tuple[str, ...]:
    result = tuple(_text(v) for v in _items(value))
    if len(set(result)) != len(result) or (required and not result):
        raise ValueError("Empty or duplicate entries")
    return result


def _integer(value: object) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("Expected positive integer")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for k, v in pairs:
        if k in result:
            raise ValueError(f"Duplicate JSON key: {k}")
        result[k] = v
    return result


def _ref(value: object, root: Path) -> ArtifactRef:
    data = _object(value)
    path, sha = _text(data.get("path")), _text(data.get("sha256"))
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        raise ValueError("Expected SHA-256 digest")
    target = confined_path(root, path)
    try:
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValueError(f"Missing artifact: {path}") from exc
    if actual != sha:
        raise ValueError(f"Artifact hash mismatch: {path}")
    return ArtifactRef(path, sha)


def _unit(value: object) -> Unit:
    d = _object(value)
    role, status = d.get("role"), d.get("status")
    if role not in ("test", "impl") or status not in ("active", "superseded"):
        raise ValueError("Invalid role or status")
    interfaces = tuple(Interface(_text(i.get("symbol")), _text(i.get("signature")))
                       for i in map(_object, _items(d.get("interfaces"))))
    return Unit(_text(d.get("id")), cast(Literal["test", "impl"], role),
                cast(Literal["active", "superseded"], status), _text(d.get("title")),
                _text(d.get("spec_ref")), _strings(d.get("owns"), required=True),
                _strings(d.get("acceptance"), required=True), _strings(d.get("depends_on")),
                interfaces, _text(d.get("instructions")),
                _text(d["add_justification"]) if "add_justification" in d else "")


def _dependencies(active: Mapping[str, Unit]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(unit_id: str) -> None:
        if unit_id in visiting:
            raise ValueError("Dependency cycle")
        if unit_id in visited:
            return
        visiting.add(unit_id)
        unit = active[unit_id]
        for dependency in unit.depends_on:
            if dependency not in active:
                raise ValueError("Dependency is not an active unit")
            if unit.role == "test" and active[dependency].role != "test":
                raise ValueError("Test author depends on implementation")
            visit(dependency)
        visiting.remove(unit_id)
        visited.add(unit_id)

    for unit_id in active:
        visit(unit_id)


def _relationships(active: Mapping[str, Unit], tests: tuple[TestLink, ...],
                   tasks: tuple[TaskLink, ...]) -> None:
    by_test = {t.test_id: t for t in tests}
    if not tests or len(by_test) != len(tests):
        raise ValueError("Missing or duplicate test links")
    for link in tests:
        author = active.get(link.author_unit)
        if author is None or author.role != "test" or link.test_id not in author.acceptance:
            raise ValueError("Invalid test author mapping")
        for unit_id in link.implementing_units:
            unit = active.get(unit_id)
            if unit is None or unit.role != "impl" or link.test_id not in unit.acceptance:
                raise ValueError("Invalid implementing unit mapping")
            if unit.spec_ref != link.criterion:
                raise ValueError("Test criterion mismatch")
    for unit in active.values():
        for test_id in unit.acceptance:
            link = by_test.get(test_id)
            if link is None or (unit.role == "impl" and unit.id not in link.implementing_units) or (
                unit.role == "test" and unit.id != link.author_unit
            ):
                raise ValueError("Acceptance missing reciprocal test link")
    if not tasks or len({t.task_ref for t in tasks}) != len(tasks):
        raise ValueError("Missing or duplicate task links")
    covered: set[str] = set()
    for task in tasks:
        if any(u not in active for u in task.unit_ids):
            raise ValueError("Task links unknown/inactive unit")
        expected = {active[u].spec_ref for u in task.unit_ids}
        if set(task.criteria) != expected:
            raise ValueError("Task criterion mismatch")
        covered.update(task.unit_ids)
    if covered != set(active):
        raise ValueError("Unmapped active unit")


def _revision(previous: Contract | None, units: tuple[Unit, ...], owners: Mapping[str, str],
              migrations: tuple[Migration, ...], rules: PathRules,
              max_added_units: int) -> Mapping[str, tuple[str, ...]]:
    current = {u.id: u for u in units}
    lineage = {u.id: (u.id,) for u in units}
    if previous is None:
        if migrations or any(u.status != "active" for u in units):
            raise ValueError("Initial contract cannot migrate or contain retired history")
        return MappingProxyType(lineage)
    prior = {u.id: u for u in previous.units}
    if not prior.keys() <= current.keys():
        raise ValueError("Historical unit removed")
    added = current.keys() - prior.keys()
    if len(added) > max_added_units or any(not current[u].add_justification for u in added):
        raise ValueError("Unjustified or excessive unit growth")
    for unit_id, old in prior.items():
        new = current[unit_id]
        if old.role != new.role or (old.status == "superseded" and old != new):
            raise ValueError("Historical role or retired record changed")
        if new.status == "superseded" and new.owns != old.owns:
            raise ValueError("Retired ownership history changed")
        lineage[unit_id] = previous.lineage_for(unit_id)
    transfers: dict[str, Migration] = {}
    for migration in migrations:
        if migration.from_unit not in prior or migration.to_unit not in current:
            raise ValueError("Unknown migration unit")
        source, dest = prior[migration.from_unit], current[migration.to_unit]
        if source.role != dest.role or dest.status != "active" or source.id == dest.id:
            raise ValueError("Invalid migration role or destination")
        for path in migration.paths:
            key = rules.normalise_path(portable_path(path))
            if key in transfers or previous.owner_of(path) != source.id or owners.get(key) != dest.id:
                raise ValueError("Invalid or duplicate migration path")
            transfers[key] = migration
        predecessors = previous.lineage_for(source.id)
        lineage[dest.id] = tuple(dict.fromkeys(predecessors + lineage[dest.id]))
    for old in previous.units:
        if old.status != "active":
            continue
        for path in old.owns:
            key = rules.normalise_path(path)
            if key not in owners:
                raise ValueError("Orphaned ownership")
            if owners[key] != old.id and key not in transfers:
                raise ValueError("Silent ownership transfer")
    return MappingProxyType(lineage)


def load_contract(raw: bytes, root: Path, rules: PathRules, *,
                  previous: Contract | None = None, max_added_units: int = 2,
                  max_cycles: int = 3, protected_paths: tuple[str, ...] = ()) -> Contract:
    """Validate bytes, referenced inputs, relationships and revision lineage.

    Limits are caller-owned run policy, never overridden from the contract.
    Resource counters are deliberately not recreated by this loader.
    """
    try:
        data = _object(json.loads(raw, object_pairs_hook=_unique_object))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed contract JSON") from exc
    version = _integer(data.get("contract_version"))
    if _integer(data.get("format_version")) != 1:
        raise ValueError("Unsupported contract format")
    digest = hashlib.sha256(raw).hexdigest()
    if version > max_cycles:
        raise ValueError("Cycle ceiling exceeded")
    if previous is None:
        if version != 1 or data.get("previous_contract_sha256") is not None:
            raise ValueError("New run must begin at version 1")
    elif version == previous.contract_version:
        if digest != previous.sha256:
            raise ValueError("Contract changed within version")
    elif version != previous.contract_version + 1 or data.get("previous_contract_sha256") != previous.sha256:
        raise ValueError("Nonconsecutive revision or wrong predecessor hash")
    module_root = portable_path(_text(data.get("module_root")))
    test_roots = _strings(data.get("test_roots"), required=True)
    for scope in test_roots:
        portable_path(scope)
    spec = _ref({"path": data.get("spec_ref"), "sha256": data.get("spec_sha256")}, root)
    presentation = _ref(data.get("presentation_ref"), root)
    coding = _ref(data.get("coding_profile_ref"), root)
    environment = _ref(data.get("environment_ref"), root)
    units = tuple(_unit(u) for u in _items(data.get("units")))
    if not units or len({u.id for u in units}) != len(units):
        raise ValueError("Missing or duplicate unit IDs")
    active = {u.id: u for u in units if u.status == "active"}
    if not active:
        raise ValueError("No active units")
    owners: dict[str, str] = {}
    protected = protected_paths + (spec.path, presentation.path, coding.path, environment.path)
    for unit in units:
        for path in unit.owns:
            key = validate_owned_path(path, (module_root,) if unit.role == "impl" else test_roots,
                                      root, rules, protected)
            if unit.status == "active":
                if key in owners:
                    raise ValueError(f"Ownership collision: {path}")
                owners[key] = unit.id
    _dependencies(active)
    tests = tuple(TestLink(_text(t.get("test_id")), _text(t.get("author_unit")),
                           _strings(t.get("implementing_units"), required=True), _text(t.get("criterion")))
                  for t in map(_object, _items(data.get("test_links"))))
    tasks = tuple(TaskLink(_text(t.get("task_ref")), _strings(t.get("unit_ids"), required=True),
                           _strings(t.get("criteria"), required=True))
                  for t in map(_object, _items(data.get("task_links"))))
    migrations = tuple(Migration(_text(m.get("from_unit")), _text(m.get("to_unit")),
                                  _strings(m.get("paths"), required=True), _text(m.get("rationale")))
                       for m in map(_object, _items(data.get("ownership_migrations"))))
    _relationships(active, tests, tasks)
    if previous is not None and version == previous.contract_version:
        # References were rechecked, even when the contract bytes are unchanged.
        return previous
    lineage = _revision(previous, units, owners, migrations, rules, max_added_units)
    return Contract(1, version, digest, _text(data.get("module")), module_root, test_roots,
                    spec, presentation, coding, environment, units, tests, tasks, migrations,
                    MappingProxyType(owners), lineage, rules)
