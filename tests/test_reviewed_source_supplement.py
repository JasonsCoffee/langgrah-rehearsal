"""Append-only coverage retains every existing assertion and owner."""
import copy
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/reviewed_source_supplement.py')
    spec=importlib.util.spec_from_file_location('reviewed_source_supplement',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def fixture():
    link={'test_id':'Old.Test','author_unit':'T','implementing_units':['I'],'criterion':'C'}
    old={'contract_version':68,'units':[{'id':'T','role':'test','owns':['Tests/Old.cs'],'acceptance':['Old.Test'],'instructions':'old'},
        {'id':'I','role':'impl','owns':['Runtime/A.cs'],'acceptance':['Old.Test'],'instructions':'impl'}],
        'test_links':[link],'test_roots':['Tests']}
    new=copy.deepcopy(old);new.update(contract_version=69,previous_contract_sha256='a'*64)
    extra=link|{'test_id':'New.Test'};paths=['Tests/New.cs','Tests/New.cs.meta']
    new['units'][0].update(owns=['Tests/Old.cs']+paths,acceptance=['Old.Test','New.Test'],instructions='new coverage')
    new['units'][1]['acceptance'].append('New.Test');new['test_links'].append(extra)
    return old,new,paths,[extra]


def test_new_coverage_can_be_appended_without_replacing_old_tests():
    old,new,paths,links=fixture();module().validate_append(old,new,'a'*64,'T',paths,links)


@pytest.mark.parametrize('bad',['replace','remove_test','new_owner','outside_root'])
def test_append_cannot_mutate_old_coverage_or_expand_scope(bad):
    old,new,paths,links=fixture()
    if bad=='replace':paths[0]='Tests/Old.cs'
    if bad=='remove_test':new['test_links'].pop(0)
    if bad=='new_owner':new['units'][1]['owns'].append('Runtime/Other.cs')
    if bad=='outside_root':paths[0]='Runtime/Bad.cs'
    with pytest.raises(ValueError):module().validate_append(old,new,'a'*64,'T',paths,links)
