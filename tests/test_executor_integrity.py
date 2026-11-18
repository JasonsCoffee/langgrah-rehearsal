"""Frozen byte preservation and restart candidate identity regressions."""

import pytest
from test_local_executor import local
from test_workspaces import workspace, git
from test_contracts import bundle
from unity_coder.core.local_executor import LocalExecutionServices


def test_owned_restore_snapshot_keeps_original_newline_bytes(local):
    executor,services,_,_,_,_=local
    path=executor.contract.units[1].owns[0]
    (services.integration.path/path).write_bytes(b"original\r\n")
    git(services.integration.path,"add","--",path)
    git(services.integration.path,"commit","-m","Fixture CRLF baseline")
    executor.advance("prepare")
    executor.advance("red")
    executor.advance("code")
    assert bytes.fromhex(services.state["snapshots"]["U1-state"][path])==b"original\r\n"


def test_service_restart_rejects_committed_candidate_drift(local):
    executor,services,workers,_,_,review=local
    executor.advance("prepare")
    path=executor.contract.units[1].owns[0]
    (services.integration.path/path).write_bytes(b"unexpected commit")
    git(services.integration.path,"add","--",path)
    git(services.integration.path,"commit","-m","Foreign drift fixture")
    with pytest.raises(ValueError,match="candidate"):
        LocalExecutionServices(services.manager,services.integration,executor.budget,workers,services.verifier,review,
                               preflight=lambda:None)
