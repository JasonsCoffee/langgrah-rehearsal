"""Frozen presentation contracts, exercised without an editor."""

from dataclasses import replace
from hashlib import sha256

import pytest

from unity_coder.core.contracts import ArtifactRef, Interface
from unity_coder.core.presentation import ArtistAsset, Presentation
from unity_coder.adapters.unity.presentation import ImportReport, validate_unity


@pytest.fixture
def baseline(tmp_path):
    files = {"UI/View.prefab": b"authored layout", "UI/View.prefab.meta": b"guid: stable",
             "UI/icon_placeHolder.png": b"placeholder", "UI/icon_placeHolder.png.meta": b"guid: icon",
             "Docs~/design.png": b"original"}
    for path, data in files.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    refs = tuple(ArtifactRef(path, sha256(data).hexdigest()) for path, data in files.items())
    asset = ArtistAsset("icon", "UI/icon_placeHolder.png", "score icon", "Docs~/design.png",
                        (64, 64), True, ("normal",), ("sprite",), ("UI/View.prefab",),
                        ("preserve dimensions and references",))
    manifest = Presentation("baseline1", refs, (Interface("View.score", "[SerializeField] int score"),),
                            ("UI/View.prefab",), (("View.score", "text"),), (asset,),
                            ("UI/View.prefab",), "Open the review scene and increment score")
    return tmp_path, manifest


def report(manifest):
    return ImportReport(manifest.identity, True, (), (), ("UI/View.prefab",),
                        (("UI/View.prefab", "stable"), ("UI/icon_placeHolder.png", "icon")))


def test_baseline_distribution_has_identical_content_and_identity(baseline, tmp_path):
    root, manifest = baseline
    manifest.validate(root)
    for name in ("unit1", "unit2", "worker"):
        copy = tmp_path / name
        manifest.distribute(root, copy)
        manifest.validate(copy)
        assert (copy / "UI/View.prefab.meta").read_bytes() == b"guid: stable"
    assert (root / "Docs~/design.png").read_bytes() == b"original"


@pytest.mark.parametrize("path", ["UI/View.prefab", "UI/View.prefab.meta", "Docs~/design.png"])
def test_frozen_content_and_generated_metadata_are_protected(baseline, path):
    root, manifest = baseline
    (root / path).write_bytes(b"changed")
    with pytest.raises(ValueError):
        manifest.validate(root)


def test_only_declared_runtime_mutations_are_permitted(baseline):
    _, manifest = baseline
    manifest.allow_mutation("View.score", "text")
    with pytest.raises(ValueError):
        manifest.allow_mutation("View.score", "hierarchy")


@pytest.mark.parametrize("field,value", [("purpose", ""), ("dimensions", (0,64)),
    ("variants", ()), ("import_requirements", ()), ("usage", ()), ("acceptance", ())])
def test_artist_delivery_requirements_are_mandatory(baseline, field, value):
    root, manifest = baseline
    broken = replace(manifest, assets=(replace(manifest.assets[0], **{field: value}),))
    with pytest.raises(ValueError):
        broken.validate(root)


def test_unity_checks_shells_import_and_reused_scene(baseline):
    root, manifest = baseline
    files = {"View.cs": "class View { [SerializeField] int score; }"}
    assert validate_unity(manifest, root, files, report(manifest), placeholder_suffix="_placeHolder") == ()
    broken = {"View.cs": "class View { int renamed; }"}
    assert validate_unity(manifest, root, broken, report(manifest), placeholder_suffix="_placeHolder")
    assert manifest.reused == ("UI/View.prefab",)


@pytest.mark.parametrize("changes", [{"launchable": False}, {"missing_scripts": ("View",)},
    {"unresolved_bindings": ("View.score",)}, {"identity": "stale"}, {"loaded_entries": ()},
    {"asset_ids": (("UI/View.prefab", "wrong"), ("UI/icon_placeHolder.png", "icon"))}])
def test_preflight_rejects_bad_import_evidence(baseline, changes):
    root, manifest = baseline
    evidence = replace(report(manifest), **changes)
    assert validate_unity(manifest, root, {"View.cs": "class View { [SerializeField] int score; }"},
                          evidence, placeholder_suffix="_placeHolder")


def test_target_placeholder_naming_is_checked(baseline):
    root, manifest = baseline
    assert validate_unity(manifest, root, {}, report(manifest), placeholder_suffix="_other")


def test_final_art_replacement_requires_separate_change_and_review(baseline):
    _, manifest = baseline
    with pytest.raises(ValueError):
        manifest.replacement("icon", separate_change=False, references_preserved=True,
                             compatible=True, reviewed=True)
    with pytest.raises(ValueError):
        manifest.replacement("icon", separate_change=True, references_preserved=True,
                             compatible=False, reviewed=True)
    with pytest.raises(ValueError):
        manifest.replacement("icon", separate_change=True, references_preserved=True,
                             compatible=True, reviewed=False)
    manifest.replacement("icon", separate_change=True, references_preserved=True,
                         compatible=True, reviewed=True)
