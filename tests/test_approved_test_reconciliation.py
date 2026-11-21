"""Frozen scope checks for the explicitly approved acceptance reconciliation."""
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/approved_test_reconciliation.py')
    spec=importlib.util.spec_from_file_location('approved_test_reconciliation',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def test_explicit_approval_and_real_contract_finding_are_required():
    m=module()
    result={'outcome':'rework','contract_version':67,'contract_sha256':m.PREVIOUS_SHA}
    dossier={'contract_version':67,'contract_sha256':m.PREVIOUS_SHA,'failed_units':[{'id':'SHELL','defect_class':'contract'}]}
    approval={'authority':'explicit_user_session','reply':m.REPLY,'version':68,'scope':m.SCOPE}
    m.validate_authority(approval,result,dossier)
    approval['reply']='pending'
    with pytest.raises(ValueError):m.validate_authority(approval,result,dossier)


def test_implementation_finding_cannot_unlock_frozen_tests():
    m=module()
    with pytest.raises(ValueError):m.validate_authority(
        {'authority':'explicit_user_session','reply':m.REPLY,'version':68,'scope':m.SCOPE},
        {'outcome':'rework','contract_version':67,'contract_sha256':m.PREVIOUS_SHA},
        {'contract_version':67,'contract_sha256':m.PREVIOUS_SHA,'failed_units':[{'id':'SHELL','defect_class':'implementation'}]})


def test_only_approved_method_bodies_can_change():
    m=module();before=b'class Fixture { [Test] public void Target() { Assert.Fail("old"); } public void Other() { Keep(); } }'
    after=before.replace(b'Assert.Fail("old");',b'Assert.True(Actual());')
    m.validate_method_change(before,after,('Target',))


@pytest.mark.parametrize('kind',['other_body','attribute','signature','using','missing','syntax'])
def test_changes_outside_approved_bodies_are_rejected(kind):
    m=module();before=b'class Fixture { [Test] public void Target() { Old(); } public void Other() { Keep(); } }'
    after=before.replace(b'Old();',b'Correct();')
    if kind=='other_body':after=after.replace(b'Keep();',b'Remove();')
    if kind=='attribute':after=after.replace(b'[Test]',b'[Ignore]')
    if kind=='signature':after=after.replace(b'void Target()',b'void Renamed()')
    if kind=='using':after=b'using Sneaky;'+after
    if kind=='missing':after=after.replace(b'Target',b'Missing')
    if kind=='syntax':after=after[:-1]
    with pytest.raises(ValueError):m.validate_method_change(before,after,('Target',))
