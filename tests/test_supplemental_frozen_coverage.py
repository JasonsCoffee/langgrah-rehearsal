"""New coverage may be added; every previously frozen assertion stays intact."""
import copy
import importlib.util
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/supplemental_frozen_coverage.py')
    s=importlib.util.spec_from_file_location('supplemental_frozen_coverage',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def case():
    old={'contract_version':65,'previous_contract_sha256':'old','test_roots':['Tests/Runtime/Script'],
        'units':[{'id':'TEST','role':'test','owns':['Tests/Runtime/Script/Old.cs'],'acceptance':['Old'],'instructions':'old'},
                 {'id':'SHELL','role':'impl','owns':['Runtime/A.cs'],'acceptance':['Old'],'instructions':'fixed'}],
        'test_links':[{'test_id':'Old','author_unit':'TEST','implementing_units':['SHELL'],'criterion':'LOBBY'}],
        'spec_sha256':'fixed'}
    paths=['Tests/Runtime/Script/New.cs','Tests/Runtime/Script/New.cs.meta']
    new=copy.deepcopy(old);new.update(contract_version=66,previous_contract_sha256='digest')
    new['units'][0]['owns']+=paths;new['units'][0]['acceptance']+=['New'];new['units'][0]['instructions']='Write only new supplement'
    new['units'][1]['acceptance']+=['New'];new['test_links'].append(old['test_links'][0]|{'test_id':'New'})
    return old,new,paths


def test_append_only_coverage_and_writable_scope():
    old,new,paths=case();module().validate_supplement(old,new,'digest','TEST',paths,'New','Old')
    assert module().new_author_paths(new['units'][0]['owns'],{'Tests/Runtime/Script/Old.cs':'hash'},paths)==tuple(paths)


@pytest.mark.parametrize('mutation',['remove_old','old_link','old_acceptance','runtime_ownership','spec','escape'])
def test_supplement_cannot_weaken_or_expand_other_scope(mutation):
    old,new,paths=case()
    if mutation=='remove_old':new['units'][0]['owns'].remove('Tests/Runtime/Script/Old.cs')
    elif mutation=='old_link':new['test_links'][0]['criterion']='changed'
    elif mutation=='old_acceptance':new['units'][0]['acceptance'].remove('Old')
    elif mutation=='runtime_ownership':new['units'][1]['owns']=['Runtime/B.cs']
    elif mutation=='spec':new['spec_sha256']='changed'
    else:paths[0]='../escape.cs'
    with pytest.raises(ValueError):module().validate_supplement(old,new,'digest','TEST',paths,'New','Old')


def test_a_frozen_path_is_never_writable_even_if_listed_as_new():
    with pytest.raises(ValueError):module().new_author_paths(['Tests/A.cs'],{'Tests/A.cs':'hash'},['Tests/A.cs'])
