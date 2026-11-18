"""Frozen backward boundary: classifications are per unit and evidence is portable."""

import json

import pytest

from test_contracts import bundle, load
from unity_coder.core.dossiers import DossierUnit, emit_dossier


def entry(unit_id, defect):
    return DossierUnit(unit_id, defect, "R7-queue-reorder", "tests",
                       (".agent/runs/run-1/evidence/test.json",), "possible interface mismatch", 2, ("RED", "STALLED"))


def test_dossier_preserves_mixed_per_unit_classifications(bundle):
    contract, root = load(bundle), bundle[1]
    relative = emit_dossier(root, "run-1", contract,
                            (entry("U1-state", "implementation"), entry("U2-system", "contract")),
                            budget_remaining={"input_tokens": 10, "output_tokens": 5, "cycles": 2})
    assert relative.as_posix() == ".agent/runs/run-1/dossier-v1.json"
    data = json.loads((root / relative).read_text())
    assert data["contract_version"] == 1 and data["contract_sha256"] == contract.sha256
    assert "defect_class" not in data and "cycle" not in data
    assert [u["defect_class"] for u in data["failed_units"]] == ["implementation", "contract"]
    assert "notes" not in json.dumps(data) and "raw_log" not in json.dumps(data)


def test_implementation_only_failure_cannot_cross_boundary(bundle):
    with pytest.raises(ValueError):
        emit_dossier(bundle[1], "run-1", load(bundle), (entry("U1-state", "implementation"),), budget_remaining={})


@pytest.mark.parametrize("run_id", ["../escape", "run/other", "run:stream", ""])
def test_dossier_run_path_is_confined(bundle, run_id):
    with pytest.raises(ValueError):
        emit_dossier(bundle[1], run_id, load(bundle), (entry("U1-state", "contract"),), budget_remaining={})


def test_budget_abandon_can_emit_without_fabricating_unit_defects(bundle):
    relative = emit_dossier(bundle[1], "run-1", load(bundle), (), reason="budget", budget_remaining={"input_tokens": 0})
    data = json.loads((bundle[1] / relative).read_text())
    assert data["reason"] == "budget" and data["failed_units"] == []
