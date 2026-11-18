"""Portable path confinement; comparison semantics belong to the adapter."""

from pathlib import Path
from typing import Protocol


class PathRules(Protocol):
    def normalise_path(self, path: str) -> str: ...
    def is_generated(self, path: str) -> bool: ...


def portable_path(value: str) -> str:
    """Reject ambiguous spellings rather than silently rewriting ownership."""
    if not value or any(c in value for c in '\\:*?"<>|'):
        raise ValueError(f"Nonportable path: {value!r}")
    parts = value.split("/")
    if any(p in ("", ".", "..") or p.endswith((" ", ".")) for p in parts):
        raise ValueError(f"Noncanonical path: {value!r}")
    if any(ord(c) < 32 for c in value):
        raise ValueError("Control character in path")
    return value


def confined_path(root: Path, relative: str) -> Path:
    """Resolve links, including existing ancestors of not-yet-created files."""
    portable_path(relative)
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative}")
    return resolved


def within(path: str, scope: str, rules: PathRules) -> bool:
    """Compare components using the adapter's selected path semantics."""
    key, bound = rules.normalise_path(path), rules.normalise_path(scope)
    return key == bound or key.startswith(bound + "/")


def validate_owned_path(path: str, scopes: tuple[str, ...], root: Path,
                        rules: PathRules, protected: tuple[str, ...]) -> str:
    """Scope/protection precede generated-file ownership exemptions."""
    resolved = confined_path(root, path).relative_to(root.resolve()).as_posix()
    if rules.normalise_path(resolved) != rules.normalise_path(path):
        raise ValueError(f"Writable ownership contains an alias: {path}")
    forbidden = ("specs", "openspec", ".git", ".agent", ".agents", ".codex", "AGENTS.md") + protected
    if any(within(path, p, rules) for p in forbidden):
        raise ValueError(f"Protected ownership: {path}")
    if not any(within(path, scope, rules) and rules.normalise_path(path) != rules.normalise_path(scope)
               for scope in scopes):
        raise ValueError(f"Ownership outside role scope: {path}")
    return rules.normalise_path(path)
