"""Frozen tests and ownership cannot change during implementation-only rework."""
import copy
import importlib.util
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/frozen_implementation_rework.py')
    s=importlib.util.spec_from_file_location('frozen_implementation_rework',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def contract():
    return {'contract_version':64,'previous_contract_sha256':'old','units':[
        {'id':'SHELL','role':'impl','instructions':'original','depends_on':[],'owns':['A.cs'],'acceptance':['T']},
        {'id':'ECON','role':'impl','instructions':'original','depends_on':[],'owns':['B.cs'],'acceptance':['T']},
        {'id':'TEST','role':'test','instructions':'fixed','depends_on':[],'owns':['Tests.cs'],'acceptance':['T']}],
        'test_links':[{'test_id':'T','implementing_units':['SHELL','ECON']}],'spec_sha256':'frozen'}


def test_only_impl_guidance_and_dependencies_may_change():
    old=contract();new=copy.deepcopy(old);new.update(contract_version=65,previous_contract_sha256='digest')
    new['units'][0]['instructions']='Repair actual compiler diagnostics'
    new['units'][1]['depends_on']=['SHELL']
    module().validate_revision(old,new,'digest')
    for field,value in [('owns',['Tests.cs']),('acceptance',[])]:
        bad=copy.deepcopy(new);bad['units'][0][field]=value
        with pytest.raises(ValueError):module().validate_revision(old,bad,'digest')


def test_test_owner_and_shared_coverage_never_change():
    old=contract();new=copy.deepcopy(old);new.update(contract_version=65,previous_contract_sha256='digest')
    new['units'][2]['instructions']='Weaken'
    with pytest.raises(ValueError):module().validate_revision(old,new,'digest')
    new=copy.deepcopy(old);new.update(contract_version=65,previous_contract_sha256='digest');new['test_links']=[]
    with pytest.raises(ValueError):module().validate_revision(old,new,'digest')


def test_shared_dependency_wave_is_supported_by_native_tdd(bundle):
    from test_contracts import load,Rules
    from test_tdd import prepare
    from unity_coder.core.tdd import TDDCoordinator
    from unity_coder.core.dispatch import ready_units
    data,root=bundle;data['units'][1]['interfaces']=[]
    c=load(bundle)
    for u in c.units:
        for name in u.owns:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'baseline')
    coordinator=TDDCoordinator(c,root,Rules());prepare(coordinator)
    assert ready_units(coordinator)==('U1-state',)
    coordinator.begin('U1-state');coordinator.pending_shared('U1-state')
    assert ready_units(coordinator)==('U2-system',)

from test_contracts import bundle
