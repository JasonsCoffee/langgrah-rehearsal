"""Hashed target policy with independently bounded writable module scopes."""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from .contracts import ArtifactRef, Contract, _integer, _items, _object, _ref, _strings, _text, _unique_object
from .ownership import PathRules, confined_path, portable_path, validate_owned_path, within


@dataclass(frozen=True)
class Source:
    source_id: str
    artifact: ArtifactRef


@dataclass(frozen=True)
class ResolvedTarget:
    host_root: Path
    game_root: Path
    mount: Path


@dataclass(frozen=True)
class TargetProfile:
    sha256: str
    host_selector: str
    game_selector: str
    allowed_mount: str
    implementation_roots: tuple[str, ...]
    test_roots: tuple[str, ...]
    rule_refs: tuple[ArtifactRef, ...]
    sources: tuple[Source, ...]
    protected_paths: tuple[str, ...]
    _game_root: Path = field(repr=False)
    _rules: PathRules = field(repr=False, compare=False)

    def resolve(self, locations: Mapping[str, Path]) -> ResolvedTarget:
        """Resolve configured selectors, never discover or launch a host."""
        try:
            host = locations[self.host_selector].resolve(strict=True)
            game = locations[self.game_selector].resolve(strict=True)
        except (KeyError, OSError) as exc:
            raise ValueError("Missing configured target location") from exc
        if host == game or not host.is_dir() or not game.is_dir():
            raise ValueError("Host and module must be distinct directories")
        if game != self._game_root:
            raise ValueError("Game location differs from validated profile")
        return ResolvedTarget(host, game, confined_path(host, self.allowed_mount))

    def validate_owned(self, path: str, role: str) -> str:
        if role not in ("impl", "test"):
            raise ValueError("Unknown ownership role")
        return validate_owned_path(path, self.implementation_roots if role == "impl" else self.test_roots,
                                   self._game_root, self._rules, self.protected_paths)

    def validate_contract(self, contract: Contract) -> None:
        """Intersect ownership with deployment policy, including generated paths."""
        if contract.coding_profile_ref.sha256 != self.sha256:
            raise ValueError("Contract references a different coding profile")
        for unit in contract.units:
            if unit.status == "active":
                for path in unit.owns:
                    self.validate_owned(path, unit.role)


def _bounded_roots(value: object, bounds: tuple[str, ...], rules: PathRules) -> tuple[str, ...]:
    roots = _strings(value, required=True)
    for root in roots:
        portable_path(root)
        if not any(within(root, portable_path(bound), rules) for bound in bounds):
            raise ValueError("Profile expands independently authorized scope")
    return roots


def load_profile(raw: bytes, game_root: Path, *, rules: PathRules, allowed_mount: str,
                 implementation_roots: tuple[str, ...], test_roots: tuple[str, ...]) -> TargetProfile:
    """Validate profile bytes against caller-owned mount and scope bounds."""
    try:
        d = _object(json.loads(raw, object_pairs_hook=_unique_object))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Malformed target profile") from exc
    if _integer(d.get("format_version")) != 1:
        raise ValueError("Unsupported profile format")
    mount = portable_path(_text(d.get("allowed_mount")))
    if rules.normalise_path(mount) != rules.normalise_path(portable_path(allowed_mount)):
        raise ValueError("Mount differs from independently authorized policy")
    host_selector, game_selector = _text(d.get("host_selector")), _text(d.get("game_selector"))
    for selector in (host_selector, game_selector):
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", selector):
            raise ValueError("Locations must use environment selector names")
    if host_selector == game_selector:
        raise ValueError("Host and game selectors must differ")
    impl = _bounded_roots(d.get("implementation_roots"), implementation_roots, rules)
    tests = _bounded_roots(d.get("test_roots"), test_roots, rules)
    rule_refs = tuple(_ref(r, game_root) for r in _items(d.get("rules")))
    sources = tuple(Source(_text(s.get("source_id")), _ref(s, game_root))
                    for s in map(_object, _items(d.get("sources"))))
    if not rule_refs or not sources or len({s.source_id for s in sources}) != len(sources):
        raise ValueError("Missing rules/sources or duplicate source identity")
    protected = _strings(d.get("protected_paths")) + tuple(r.path for r in rule_refs) + tuple(s.artifact.path for s in sources)
    for path in protected:
        confined_path(game_root, path)
    return TargetProfile(hashlib.sha256(raw).hexdigest(), host_selector, game_selector,
                         mount, impl, tests, rule_refs, sources, protected, game_root.resolve(), rules)
