"""Frozen target-policy tests; target facts are input, never core constants."""

import hashlib
import json
from pathlib import Path

import pytest

from unity_coder.core.target_profiles import load_profile


class Rules:
    def normalise_path(self, path):
        return path

    def is_generated(self, path):
        return path.endswith(".meta")


@pytest.fixture
def profile_bundle(tmp_path):
    game = tmp_path / "external-game"
    game.mkdir()
    (game / "AGENTS.md").write_bytes(b"No shared edits")
    (game / "Docs~").mkdir()
    (game / "Docs~/design.md").write_bytes(b"Original design")
    def ref(path):
        return {"path": path, "sha256": hashlib.sha256((game / path).read_bytes()).hexdigest()}
    data = {
        "format_version": 1, "host_selector": "UNITY_HOST", "game_selector": "GAME_ROOT",
        "allowed_mount": "Assets/JJGame/monopoly", "implementation_roots": ["Runtime/Script"],
        "test_roots": ["Tests/Runtime/Script"], "rules": [ref("AGENTS.md")],
        "sources": [{"source_id": "design:original", **ref("Docs~/design.md")}],
        "protected_paths": ["Docs~", ".codex", "openspec", "Runtime/Resource"],
    }
    return data, game


def load(bundle):
    data, game = bundle
    return load_profile(json.dumps(data).encode(), game, rules=Rules(),
                        allowed_mount="Assets/JJGame/monopoly",
                        implementation_roots=("Runtime/Script",), test_roots=("Tests/Runtime/Script",))


def test_profile_separates_machine_locations_and_preserves_provenance(profile_bundle, tmp_path):
    profile = load(profile_bundle)
    host = tmp_path / "dedicated-host"
    host.mkdir()
    resolved = profile.resolve({"UNITY_HOST": host, "GAME_ROOT": profile_bundle[1]})
    assert resolved.game_root == profile_bundle[1].resolve()
    assert resolved.host_root == host.resolve()
    assert resolved.mount == host / "Assets/JJGame/monopoly"
    assert profile.sources[0].source_id == "design:original"
    assert profile.sources[0].artifact.sha256 == profile_bundle[0]["sources"][0]["sha256"]
    assert profile.sha256 == hashlib.sha256(json.dumps(profile_bundle[0]).encode()).hexdigest()


@pytest.mark.parametrize("change", ["mount", "wide_impl", "wide_tests", "rule_hash", "source_hash", "source_id", "empty_rules", "empty_sources", "bad_selector", "version"])
def test_profile_cannot_expand_policy_or_lose_provenance(profile_bundle, change):
    d, game = profile_bundle
    if change == "mount": d["allowed_mount"] = "Assets/JJGame/shared"
    elif change == "wide_impl": d["implementation_roots"] = ["Runtime"]
    elif change == "wide_tests": d["test_roots"] = ["Tests"]
    elif change == "rule_hash": (game / "AGENTS.md").write_bytes(b"Changed rule")
    elif change == "source_hash": d["sources"][0]["sha256"] = "0" * 64
    elif change == "source_id": d["sources"].append(dict(d["sources"][0]))
    elif change == "empty_rules": d["rules"] = []
    elif change == "empty_sources": d["sources"] = []
    elif change == "bad_selector": d["host_selector"] = "../host"
    elif change == "version": d["format_version"] = 2
    with pytest.raises(ValueError):
        load(profile_bundle)


@pytest.mark.parametrize("path,role", [
    ("Runtime/Script/Game.cs", "impl"), ("Tests/Runtime/Script/GameTests.cs", "test"),
])
def test_module_relative_paths_allowed(profile_bundle, path, role):
    assert load(profile_bundle).validate_owned(path, role) == path


@pytest.mark.parametrize("path,role", [
    ("../shared/Shared.cs", "impl"), ("Assets/JJGame/other/File.cs", "impl"),
    ("Packages/manifest.json", "impl"), ("ProjectSettings/Settings.asset", "impl"),
    ("Docs~/design.md", "impl"), ("Runtime/Resource/Icon.meta", "impl"),
    ("Runtime/Script/Test.cs", "test"), ("Tests/Runtime/Script/Test.cs", "impl"),
])
def test_profile_rejects_shared_protected_and_wrong_role_paths(profile_bundle, path, role):
    with pytest.raises(ValueError):
        load(profile_bundle).validate_owned(path, role)


def test_host_and_game_cannot_alias(profile_bundle):
    with pytest.raises(ValueError):
        load(profile_bundle).resolve({"UNITY_HOST": profile_bundle[1], "GAME_ROOT": profile_bundle[1]})


def test_missing_location_does_not_guess_a_host(profile_bundle):
    with pytest.raises(ValueError):
        load(profile_bundle).resolve({"GAME_ROOT": profile_bundle[1]})
