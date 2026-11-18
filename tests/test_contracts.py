"""Frozen Phase 1 behavioral acceptance: contracts are untrusted inputs."""

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from unity_coder.core.contracts import load_contract


class Rules:
    def __init__(self, insensitive=False):
        self.insensitive = insensitive

    def normalise_path(self, path):
        return path.casefold() if self.insensitive else path

    def is_generated(self, path):
        return path.endswith(".meta")


@pytest.fixture
def bundle(tmp_path):
    data = json.loads(Path("tests/fixtures/contracts/valid.json").read_text())
    spec = tmp_path / data["spec_ref"]
    spec.parent.mkdir(parents=True)
    spec.write_bytes(b"R7-queue-reorder: preserve identity")
    data["spec_sha256"] = hashlib.sha256(spec.read_bytes()).hexdigest()
    for key in ("presentation_ref", "coding_profile_ref", "environment_ref"):
        ref = data[key]
        target = tmp_path / ref["path"]
        target.write_bytes(b"{}")
        ref["sha256"] = hashlib.sha256(b"{}").hexdigest()
    return data, tmp_path


def load(bundle, rules=None, **options):
    data, root = bundle
    return load_contract(json.dumps(data).encode(), root, rules or Rules(), **options)


def test_valid_shared_contract_has_immutable_identity(bundle):
    c = load(bundle)
    assert c.contract_version == 1
    assert c.format_version == 1
    assert c.sha256 == hashlib.sha256(json.dumps(bundle[0]).encode()).hexdigest()
    assert c.test_links[0].implementing_units == ("U1-state", "U2-system")
    assert c.task_links[0].unit_ids == ("U0-tests", "U1-state", "U2-system")
    assert c.owner_of("Runtime/Script/Queue/DinerState.cs") == "U1-state"
    with pytest.raises((AttributeError, TypeError)):
        c.contract_version = 2


@pytest.mark.parametrize("change", [
    "empty_owns", "collision", "duplicate_id", "missing_dependency", "dependency_cycle",
    "test_depends_on_impl", "missing_acceptance", "unknown_test", "bad_author",
    "missing_implementer", "unknown_task_unit", "missing_task_criterion",
    "unsupported_format", "boolean_version", "bad_role", "bad_status", "duplicate_test",
    "missing_task_link", "missing_profile", "profile_hash", "spec_hash",
])
def test_invalid_contract_is_rejected(bundle, change):
    d, root = bundle
    units = d["units"]
    if change == "empty_owns": units[1]["owns"] = []
    elif change == "collision": units[2]["owns"] = units[1]["owns"][:]
    elif change == "duplicate_id": units[2]["id"] = units[1]["id"]
    elif change == "missing_dependency": units[1]["depends_on"] = ["missing"]
    elif change == "dependency_cycle": units[1]["depends_on"] = ["U2-system"]
    elif change == "test_depends_on_impl": units[0]["depends_on"] = ["U1-state"]
    elif change == "missing_acceptance": units[1]["acceptance"] = []
    elif change == "unknown_test": units[1]["acceptance"] = ["Missing.Test"]
    elif change == "bad_author": d["test_links"][0]["author_unit"] = "U1-state"
    elif change == "missing_implementer": d["test_links"][0]["implementing_units"] = ["missing"]
    elif change == "unknown_task_unit": d["task_links"][0]["unit_ids"] = ["missing"]
    elif change == "missing_task_criterion": d["task_links"][0]["criteria"] = ["wrong"]
    elif change == "unsupported_format": d["format_version"] = 2
    elif change == "boolean_version": d["contract_version"] = True
    elif change == "bad_role": units[1]["role"] = "architect"
    elif change == "bad_status": units[1]["status"] = "finished"
    elif change == "duplicate_test": d["test_links"].append(copy.deepcopy(d["test_links"][0]))
    elif change == "missing_task_link": d["task_links"] = []
    elif change == "missing_profile": (root / d["coding_profile_ref"]["path"]).unlink()
    elif change == "profile_hash": d["environment_ref"]["sha256"] = "0" * 64
    elif change == "spec_hash": (root / d["spec_ref"]).write_bytes(b"changed")
    with pytest.raises(ValueError):
        load(bundle)


@pytest.mark.parametrize("path", [
    "../shared/file.cs", "Runtime/Script/Queue/../../../../escape.cs",
    "specs/feature/contract.json", "openspec/config.yaml", ".git/config",
    ".agent/run.json", "AGENTS.md", "Runtime/Script/Queue/./File.cs",
    "Runtime//Script/Queue/File.cs", "Runtime\\Script\\Queue\\File.cs",
    "Runtime/Script/QueueX/File.cs", "Tests/Runtime/Script/Test.cs",
    "Runtime/Script/Queue/file.cs:stream", "Runtime/Script/Queue/*.cs",
])
def test_paths_are_confined_and_canonical(bundle, path):
    bundle[0]["units"][1]["owns"] = [path]
    with pytest.raises(ValueError):
        load(bundle)


def test_protected_scope_cannot_be_authorized_by_contract(bundle):
    bundle[0]["module_root"] = "specs"
    bundle[0]["units"][1]["owns"] = [bundle[0]["spec_ref"]]
    with pytest.raises(ValueError):
        load(bundle)


def test_adapter_selects_case_semantics(bundle):
    bundle[0]["units"][2]["owns"] = ["Runtime/Script/Queue/dinerstate.cs"]
    assert load(bundle).owner_of("Runtime/Script/Queue/dinerstate.cs") == "U2-system"
    with pytest.raises(ValueError):
        load(bundle, Rules(insensitive=True))


def test_generated_claim_cannot_escape_protected_scope(bundle):
    bundle[0]["units"][1]["owns"] = ["specs/plan.meta"]
    with pytest.raises(ValueError):
        load(bundle)


def test_same_version_requires_identical_bytes(bundle):
    first = load(bundle)
    assert load(bundle, previous=first).sha256 == first.sha256
    bundle[0]["units"][1]["instructions"] = "changed"
    with pytest.raises(ValueError):
        load(bundle, previous=first)


def revision(bundle):
    first = load(bundle)
    d = bundle[0]
    d["contract_version"] = 2
    d["previous_contract_sha256"] = first.sha256
    return first


@pytest.mark.parametrize("change", ["skip", "wrong_previous", "remove", "silent_transfer", "orphan", "growth", "no_justification"])
def test_invalid_revision_is_rejected(bundle, change):
    first = revision(bundle)
    d = bundle[0]
    if change == "skip": d["contract_version"] = 3
    elif change == "wrong_previous": d["previous_contract_sha256"] = "0" * 64
    elif change == "remove": d["units"].pop()
    elif change == "silent_transfer":
        d["units"][1]["owns"], d["units"][2]["owns"] = d["units"][2]["owns"], d["units"][1]["owns"]
    elif change == "orphan": d["units"][1]["owns"] = ["Runtime/Script/Queue/New.cs"]
    else:
        for n in range(3 if change == "growth" else 1):
            added = copy.deepcopy(d["units"][1])
            added.update(id=f"new{n}", owns=[f"Runtime/Script/Queue/New{n}.cs"])
            if change == "growth": added["add_justification"] = "split responsibility"
            d["units"].append(added)
    with pytest.raises(ValueError):
        load(bundle, previous=first, max_added_units=2)


def test_explicit_migration_retains_history_and_current_owner(bundle):
    first = revision(bundle)
    d = bundle[0]
    old = d["units"][1]
    new = copy.deepcopy(old)
    new.update(id="U3-state", add_justification="replace infeasible unit")
    old["status"] = "superseded"
    d["units"].append(new)
    d["units"][2]["depends_on"] = ["U3-state"]
    for link in d["test_links"]:
        link["implementing_units"] = ["U3-state" if u == "U1-state" else u for u in link["implementing_units"]]
    d["task_links"][0]["unit_ids"] = ["U0-tests", "U3-state", "U2-system"]
    d["ownership_migrations"] = [{"from_unit": "U1-state", "to_unit": "U3-state", "paths": old["owns"][:], "rationale": "replacement"}]
    second = load(bundle, previous=first)
    assert second.owner_of(old["owns"][0]) == "U3-state"
    assert second.units[1].status == "superseded"
    assert first.units[1].status == "active"
    assert second.lineage_for("U3-state") == ("U1-state", "U3-state")


def test_cycle_ceiling_cannot_reset_by_revising(bundle):
    first = revision(bundle)
    with pytest.raises(ValueError):
        load(bundle, previous=first, max_cycles=1)


def test_new_run_cannot_start_at_later_version(bundle):
    bundle[0]["contract_version"] = 2
    with pytest.raises(ValueError):
        load(bundle)


def test_duplicate_json_keys_rejected(bundle):
    raw = json.dumps(bundle[0]).encode()
    raw = raw.replace(b'"format_version": 1', b'"format_version": 99, "format_version": 1')
    with pytest.raises(ValueError):
        load_contract(raw, bundle[1], Rules())


def test_reference_symlink_escape_rejected(bundle, tmp_path):
    data, root = bundle
    outside = root.parent / (root.name + "-outside")
    outside.mkdir()
    (outside / "profile.json").write_bytes(b"{}")
    link = root / "linked"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], check=True, capture_output=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    data["coding_profile_ref"]["path"] = "linked/profile.json"
    with pytest.raises(ValueError):
        load(bundle)
