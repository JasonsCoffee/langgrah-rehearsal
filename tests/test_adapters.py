"""Structural C# tests execute only the grammar, never Unity or a compiler."""

from pathlib import Path

import pytest

from unity_coder.adapters.unity import UnityAdapter
from unity_coder.core.contracts import Interface


@pytest.fixture
def files():
    return {"Runtime/View.cs": Path("tests/fixtures/csharp/View.cs").read_text()}


def test_valid_source_parses_without_unity(files):
    assert UnityAdapter().parse_check(files) == ()


@pytest.mark.parametrize("source", ["class X {", "class X { void M( { } }", "namespace G { class X { int a = ; } }"])
def test_parse_errors_identify_file(source):
    violations = UnityAdapter().parse_check({"Code/X.cs": source})
    assert violations
    assert all(v.file == "Code/X.cs" and v.code == "syntax" and v.message for v in violations)


def test_missing_semicolon_is_not_a_false_parse_pass():
    assert UnityAdapter().parse_check({"Code/X.cs": "class X { int count }"})


def test_matching_signatures_and_serialized_field(files):
    assert UnityAdapter().check_interfaces(files, (
        Interface("Game.View.ReorderQueue", "ReorderQueue(int from, int to)"),
        Interface("Game.View.score", "[SerializeField] int score"),
    )) == ()


@pytest.mark.parametrize("mutation,symbol,signature", [
    ("parameter", "Game.View.ReorderQueue", "ReorderQueue(int from, int to)"),
    ("method", "Game.View.SetScore", "SetScore(int value)"),
    ("field_name", "Game.View.score", "[SerializeField] int score"),
    ("field_type", "Game.View.score", "[SerializeField] int score"),
    ("serialization", "Game.View.score", "[SerializeField] int score"),
    ("class", "Game.View.SetScore", "SetScore(int value)"),
])
def test_frozen_interfaces_reject_mutations(files, mutation, symbol, signature):
    source = files["Runtime/View.cs"]
    if mutation == "parameter": source = source.replace("int from", "float from")
    elif mutation == "method": source = source.replace("SetScore", "DisplayScore")
    elif mutation == "field_name": source = source.replace("score", "points")
    elif mutation == "field_type": source = source.replace("int score", "string score")
    elif mutation == "serialization": source = source.replace("[SerializeField]", "")
    elif mutation == "class": source = source.replace("class View", "class Other")
    violations = UnityAdapter().check_interfaces({"Runtime/View.cs": source}, (Interface(symbol, signature),))
    assert violations
    assert violations[0].symbol == symbol
    assert violations[0].file == "Runtime/View.cs"


def test_body_changes_and_whitespace_do_not_break_interface(files):
    files["Runtime/View.cs"] = files["Runtime/View.cs"].replace("score = value;", "score = value + 1;").replace("int from, int to", "int   from ,\n int to")
    assert UnityAdapter().check_interfaces(files, (Interface("View.ReorderQueue", "ReorderQueue(int from, int to)"),)) == ()


def test_file_scoped_namespace_and_overloads():
    source = "namespace Game; public class V { public void M(int value) {} public void M(string value) {} }"
    assert UnityAdapter().check_interfaces({"V.cs": source}, (Interface("Game.V.M", "M(string value)"),)) == ()
    assert UnityAdapter().check_interfaces({"V.cs": source}, (Interface("Game.V.M", "M(float value)"),))


def test_comment_cannot_fake_a_signature():
    source = "class V { /* public void M(int value) {} */ }"
    assert UnityAdapter().check_interfaces({"V.cs": source}, (Interface("V.M", "M(int value)"),))


@pytest.mark.parametrize("path", ["Runtime/View.cs.meta", "obj/Debug/File.cs", "Runtime/obj/Generated.cs", "Runtime/View.g.cs", "Runtime/View_generated.cs"])
def test_generated_paths_are_adapter_owned_policy(path):
    assert UnityAdapter().is_generated(path)


def test_generated_status_does_not_bypass_frozen_interfaces():
    adapter = UnityAdapter()
    assert adapter.is_generated("View.g.cs")
    assert adapter.check_interfaces({"View.g.cs": "class View { }"}, (Interface("View.score", "[SerializeField] int score"),))


def test_case_rules_are_explicit():
    assert UnityAdapter(case_sensitive=False).normalise_path("Runtime/View.cs") == "runtime/view.cs"
    assert UnityAdapter(case_sensitive=True).normalise_path("Runtime/View.cs") == "Runtime/View.cs"
    assert not UnityAdapter().is_generated("Runtime/Object.cs")
