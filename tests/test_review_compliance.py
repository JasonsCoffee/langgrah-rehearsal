"""Review regressions, authored before fixes; all dependencies are local fakes."""
from dataclasses import replace
from hashlib import sha256
import json

import pytest

from test_contracts import bundle
from test_workspaces import workspace, git
from test_local_executor import local
from unity_coder.core.contracts import ArtifactRef
from unity_coder.core.workspaces import WorkspaceCandidate


def configure_rules(services):
    rule_path='rules/module.md'
    rule=(services.integration.path/rule_path)
    rule.parent.mkdir()
    rule.write_text('Use the existing lifecycle and release subscriptions.',encoding='utf-8')
    payload=json.dumps({'rules':[{'path':rule_path,'sha256':sha256(rule.read_bytes()).hexdigest()}]}).encode()
    ref=services.contract.coding_profile_ref
    (services.integration.path/ref.path).write_bytes(payload)
    services.contract=replace(services.contract,coding_profile_ref=ArtifactRef(ref.path,sha256(payload).hexdigest()))
    return rule_path


def test_coding_context_includes_hashed_profile_and_rule_text(local):
    _,services,*_=local
    rule=configure_rules(services)
    context=services._context()
    assert services.contract.coding_profile_ref.path in context
    assert context[rule]=='Use the existing lifecycle and release subscriptions.'


def test_coding_context_rejects_rule_drift_before_dispatch(local):
    _,services,*_=local
    rule=configure_rules(services)
    (services.integration.path/rule).write_text('Different rule',encoding='utf-8')
    with pytest.raises(ValueError,match='hash'):
        services._context()


def test_coding_context_rejects_profile_drift_before_dispatch(local):
    _,services,*_=local
    configure_rules(services)
    (services.integration.path/services.contract.coding_profile_ref.path).write_bytes(b'{}')
    with pytest.raises(ValueError,match='hash'):
        services._context()


def test_unchanged_restoration_does_not_attempt_an_empty_commit(workspace):
    manager,_,base,contract=workspace
    integration=manager.create_integration(1,base)
    unit=next(u for u in contract.units if u.role=='impl')
    path=unit.owns[0]
    candidate=WorkspaceCandidate(unit.id,contract.sha256,base,{},
        {path:(integration.path/path).read_bytes()})
    assert manager.integrate(integration,candidate,{})==base
    assert git(integration.path,'status','--porcelain')==''
