"""Additional frozen boundary replay and CLI checks."""

import json

import pytest

from test_architect_boundary import boundary, planning, result
from test_contracts import bundle
from unity_coder.core.progress import ProgressStore


def test_live_progress_reconnect_never_requests_a_fresh_start(planning, tmp_path):
    b = boundary(planning, tmp_path)
    ProgressStore(b.state_root, b.run_id, contract_version=1, contract_sha256=b.contract.sha256).publish(
        "coding", units={"U1-state": "green"})
    calls = []
    b.invoke(lambda action: (calls.append(action), result(b)))
    assert calls == ["resume"]


def test_terminal_result_never_dispatches_again(planning, tmp_path):
    b = boundary(planning, tmp_path)
    result(b, "abandon")
    calls = []
    b.invoke(lambda action: calls.append(action))
    assert calls == []


def test_context_identity_is_immutable_across_reconnect(planning, tmp_path):
    boundary(planning, tmp_path)
    planning[0]["schemaName"] = "changed-schema"
    with pytest.raises(ValueError, match="identity|provenance"):
        boundary(planning, tmp_path)


def test_cli_exports_context_without_creating_a_planning_system(planning, capsys):
    from unity_coder.cli import main
    payload, sources, _, root = planning
    (root / "instructions.json").write_text(json.dumps(payload))
    (root / "sources.json").write_text(json.dumps(sources))
    code = main(["export-context", "--root", str(root), "--instructions", "instructions.json",
                 "--sources", "sources.json"])
    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["format_version"] == 1
    assert output["schema"] == "custom-existing"
    assert not (root / "openspec").exists()


def test_cli_reports_invalid_input_without_a_traceback(planning, capsys):
    from unity_coder.cli import main
    root = planning[3]
    code = main(["export-context", "--root", str(root), "--instructions", "missing.json",
                 "--sources", "missing.json"])
    assert code == 2
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "operational"
    assert "Traceback" not in str(output)
    assert str(root) not in str(output)
