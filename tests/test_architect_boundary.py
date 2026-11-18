"""Frozen delegated-apply boundary acceptance; no editor or provider required."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from test_contracts import bundle, load
from unity_coder.core.architect_boundary import ArchitectBoundary, discover_context
from unity_coder.core.lifecycle import RunLifecycle
from unity_coder.core.progress import ProgressStore


@pytest.fixture
def planning(bundle):
    data, root = bundle
    paths = {
        "planning/work.md": b"- [ ] Deliver queue\n- [ ] Other work\n",
        "design/original.md": b"Original design",
        "wiki/index.md": b"Derived navigation",
        "rules/coding.md": b"Owned game files only",
    }
    for path, content in paths.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    payload = {
        "root": {"path": str(root)}, "changeName": "queue-reorder",
        "schemaName": "custom-existing", "state": "ready",
        "contextFiles": {"work-items": [str(root / "planning/work.md")]},
        "tasks": [
            {"id": "1.1", "description": "Deliver queue", "done": False,
             "sourcePath": str(root / "planning/work.md"), "line": 1},
            {"id": "1.2", "description": "Other work", "done": False,
             "sourcePath": str(root / "planning/work.md"), "line": 2},
        ],
    }
    data["task_links"][0]["task_ref"] = "queue-reorder:1.1"
    sources = {"design": "design/original.md", "wiki": "wiki/index.md", "rules": "rules/coding.md"}
    return payload, sources, load(bundle), root


def boundary(planning, tmp_path):
    payload, sources, contract, root = planning
    context = discover_context(root, payload, sources=sources)
    return ArchitectBoundary(root, tmp_path / "state", "run-1", contract, context)


def result(b, outcome="operational"):
    return RunLifecycle(b.state_root, b.run_id, contract_version=b.contract.contract_version,
                        contract_sha256=b.contract.sha256).finish(
        outcome, candidate_revision="candidate", reason="test seam", evidence_refs=())


def test_schema_discovery_exports_portable_hashed_provenance(planning):
    payload, sources, _, root = planning
    context = discover_context(root, payload, sources=sources)
    wire = context.to_dict()
    assert wire["schema"] == "custom-existing"
    assert wire["artifacts"]["work-items"][0]["path"] == "planning/work.md"
    assert wire["sources"]["design"]["sha256"] == sha256(b"Original design").hexdigest()
    assert set(wire["sources"]) == {"design", "wiki", "rules"}
    assert wire["tasks"][0]["task_ref"] == "queue-reorder:1.1"
    assert str(root) not in json.dumps(wire)
    assert not (root / "openspec").exists()


@pytest.mark.parametrize("mutation", ["no-root", "blocked", "escape", "missing", "stale-task", "duplicate-task"])
def test_discovery_rejects_invalid_or_stale_inputs(planning, mutation):
    payload, sources, _, root = planning
    if mutation == "no-root":
        payload["root"] = None
    elif mutation == "blocked":
        payload["state"] = "blocked"
    elif mutation == "escape":
        payload["contextFiles"]["work-items"] = ["../outside.md"]
    elif mutation == "missing":
        sources["rules"] = "missing.md"
    elif mutation == "stale-task":
        payload["tasks"][0]["description"] = "Different task"
    else:
        payload["tasks"].append(deepcopy(payload["tasks"][0]))
    with pytest.raises(ValueError):
        discover_context(root, payload, sources=sources)


def test_unknown_task_link_rejected(planning, tmp_path):
    planning[0]["tasks"][0]["id"] = "other"
    with pytest.raises(ValueError, match="task"):
        boundary(planning, tmp_path)


def test_changed_provenance_blocks_execution(planning, tmp_path):
    b = boundary(planning, tmp_path)
    (planning[3] / "rules/coding.md").write_bytes(b"Changed")
    calls = []
    with pytest.raises(ValueError, match="changed"):
        b.invoke(lambda action: calls.append(action))
    assert calls == []


def test_executor_cannot_change_planning_silently(planning, tmp_path):
    b = boundary(planning, tmp_path)
    def execute(action):
        (planning[3] / "planning/work.md").write_bytes(b"- [x] Deliver queue\n")
        result(b)
    with pytest.raises(ValueError, match="changed"):
        b.invoke(execute)


@pytest.mark.parametrize("outcome", ["operational", "cancelled", "rework", "abandon", "awaiting_human_review"])
def test_structured_results_never_complete_tasks_without_acceptance(planning, tmp_path, outcome):
    b = boundary(planning, tmp_path)
    calls = []
    def execute(action):
        calls.append(action)
        result(b, outcome)
    report = b.invoke(execute)
    assert calls == ["start"]
    assert report["result"]["outcome"] == outcome
    assert report["eligible_tasks"] == []
    assert (planning[3] / "planning/work.md").read_bytes().startswith(b"- [ ]")


@pytest.mark.parametrize("field,value", [("format_version", 2), ("contract_sha256", "wrong"),
                                        ("run_id", "another"), ("outcome", "success")])
def test_result_identity_and_format_are_checked(planning, tmp_path, field, value):
    b = boundary(planning, tmp_path)
    record = result(b)
    record[field] = value
    (b.state_root / ".agent/runs/run-1/result.json").write_text(json.dumps(record))
    with pytest.raises(ValueError):
        b.observe()


def test_reconnect_reads_progress_without_inventing_a_result(planning, tmp_path):
    b = boundary(planning, tmp_path)
    progress = ProgressStore(b.state_root, b.run_id, contract_version=1, contract_sha256=b.contract.sha256)
    progress.publish("complete", units={"U1-state": "complete"})
    report = boundary(planning, tmp_path).observe()
    assert report["progress"]["sequence"] == 1
    assert report["result"] is None
    assert report["eligible_tasks"] == []


def review(b, decision):
    result(b, "awaiting_human_review")
    record = {"decision": decision, "reviewer": "human-1", "candidate_revision": "candidate",
              "request": {"run_id": b.run_id, "contract_version": 1,
                          "contract_sha256": b.contract.sha256, "candidate_revision": "candidate"}}
    path = b.state_root / ".agent/runs/run-1/review.json"
    path.write_text(json.dumps(record))
    return record


@pytest.mark.parametrize("decision,action", [("implementation", "repair"), ("accept", "finalize")])
def test_review_resume_routes_existing_contract_without_self_approval(planning, tmp_path, decision, action):
    b = boundary(planning, tmp_path)
    review(b, decision)
    calls = []
    b.invoke(lambda requested: (calls.append(requested), result(b)))
    assert calls == [action]


def test_contract_review_ends_invocation_and_does_not_dispatch(planning, tmp_path):
    b = boundary(planning, tmp_path)
    review(b, "contract")
    calls = []
    report = b.invoke(lambda action: calls.append(action))
    assert calls == []
    assert report["next_action"] == "rework"
    assert report["eligible_tasks"] == []


def test_forged_or_stale_pass_cannot_reconcile(planning, tmp_path):
    b = boundary(planning, tmp_path)
    record = result(b)
    record.update(outcome="pass", approved_parent="candidate", reviewer="human-1",
                  review_ref=".agent/runs/run-1/review.json")
    path = b.state_root / ".agent/runs/run-1/result.json"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        b.observe()
    review(b, "accept")
    record["approved_parent"] = "stale"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        b.observe()


def test_accepted_pass_only_reconciles_mapped_tasks_and_never_writes_planning(planning, tmp_path):
    b = boundary(planning, tmp_path)
    review(b, "accept")
    record = result(b)
    record.update(outcome="pass", approved_parent="candidate", candidate_revision="completion",
                  reviewer="human-1", review_ref=".agent/runs/run-1/review.json")
    (b.state_root / ".agent/runs/run-1/result.json").write_text(json.dumps(record))
    report = b.observe()
    assert report["eligible_tasks"] == ["queue-reorder:1.1"]
    assert report["unmapped_tasks"] == ["queue-reorder:1.2"]
    assert (planning[3] / "planning/work.md").read_bytes() == b"- [ ] Deliver queue\n- [ ] Other work\n"
