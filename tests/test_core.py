"""Unit tests for the dependency-free core: log parsing and ownership."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from unity_coder.contract import ContractError, assert_owned, load_contract, validate_units
from unity_coder.models import extract_json
from unity_coder.unity import parse_compile_errors


def test_parse_compile_errors_extracts_and_dedupes():
    log = """
Assets/_Project/Scripts/Queue/QueueSystem.cs(42,17): error CS0246: The type or namespace name 'Tray' could not be found
Assets/_Project/Scripts/Queue/QueueSystem.cs(42,17): error CS0246: The type or namespace name 'Tray' could not be found
Assets/_Project/Scripts/Tray/TrayView.cs(9,5): error CS0103: The name 'Foo' does not exist
"""
    errors = parse_compile_errors(log)
    assert len(errors) == 2
    assert "QueueSystem.cs:42 [CS0246]" in errors[0]
    assert "TrayView.cs:9 [CS0103]" in errors[1]


def test_parse_compile_errors_ignores_warnings_and_clean_logs():
    log = "Assets/Foo.cs(1,1): warning CS0169: unused field\nAll good\n"
    assert parse_compile_errors(log) == []


def test_ownership_collision_is_rejected():
    units = [
        {"id": "U1", "instructions": "a", "owns": ["Assets/Scripts/DinerState.cs"]},
        {"id": "U2", "instructions": "b", "owns": ["Assets/Scripts/DinerState.cs"]},
    ]
    with pytest.raises(ContractError, match="ownership collision"):
        validate_units(units)


def test_units_without_owned_paths_are_rejected():
    with pytest.raises(ContractError, match="no owned paths"):
        validate_units([{"id": "U1", "instructions": "a", "owns": []}])


def test_assert_owned_supports_globs():
    unit = {"id": "U1", "instructions": "a", "owns": ["Assets/Tests/EditMode/*.cs"]}
    assert_owned(unit, "Assets/Tests/EditMode/QueueSystemTests.cs")
    with pytest.raises(ContractError, match="does not own"):
        assert_owned(unit, "Assets/Scripts/QueueSystem.cs")


def test_load_contract_accepts_both_shapes(tmp_path: Path):
    unit = {"id": "U1", "instructions": "a", "owns": ["Assets/A.cs"]}
    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps([unit]), encoding="utf-8")
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps({"units": [unit]}), encoding="utf-8")

    assert load_contract(bare)[0]["id"] == "U1"
    assert load_contract(wrapped)[0]["id"] == "U1"


def test_extract_json_handles_fenced_output():
    raw = 'Sure, here it is:\n```json\n{"patches": [], "ok": true}\n```\n'
    assert extract_json(raw)["ok"] is True
