"""Compiler facts may route only unfrozen test authors back to preparation."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from unity_coder.core.executor import StepResult


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/baseline_compile_route.py')
    s=importlib.util.spec_from_file_location('baseline_compile_route',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fact():
    return {'gate':'compile','status':'failed','test_result':None,
        'request':{'candidate_revision':'candidate','full_suite':True,'contract_version':62,'contract_sha256':'contract','test_selection':['Test.A']},
        'violations':[{'file':'Assets/JJGame/monopoly/Tests/A.cs','code':'compile','message':'CS0535 missing Context'}]}


def contract():
    return SimpleNamespace(contract_version=62,sha256='contract',
        units=[SimpleNamespace(id='TEST-A',role='test',status='active',owns=('Tests/A.cs',))],
        test_links=[SimpleNamespace(test_id='Test.A')])


def test_only_actual_full_baseline_test_compile_failure_has_an_author():
    assert module().compile_authors(fact(),contract(),'candidate')==('TEST-A',)


@pytest.mark.parametrize('bad',['frozen-behavior','not-compile','different-candidate','different-contract','partial','outside','impl'])
def test_changed_or_unattributable_fact_is_rejected(bad):
    f=fact();c=contract()
    if bad=='frozen-behavior':f['test_result']={'executed':['Test.A']}
    elif bad=='not-compile':f['gate']='tests'
    elif bad=='different-candidate':f['request']['candidate_revision']='other'
    elif bad=='different-contract':f['request']['contract_sha256']='other'
    elif bad=='partial':f['request']['full_suite']=False
    elif bad=='outside':f['violations'][0]['file']='Assets/Shared.cs'
    else:c.units[0].role='impl'
    with pytest.raises(ValueError):module().compile_authors(f,c,'candidate')


class Inner:
    def __init__(self):
        self.count=1;self.tdd=SimpleNamespace(frozen=False,record_preparation_failure=self.failed,
            state=lambda _:SimpleNamespace(preparation_attempts=self.count,stage='test_authoring'))
        self.state={};self.saved=0;self.delegated=[]
    def failed(self,_):self.count+=1
    def _save(self):self.saved+=1;return {'count':self.count}
    def _statuses(self):return {'TEST-A':'test_authoring'}
    def preflight(self):pass
    def step(self,stage,operation):self.delegated.append((stage,operation));return StepResult('red',{})
    def reconcile(self,stage,operation):return self.step(stage,operation)


def test_route_is_legal_once_durable_and_never_claims_execution(tmp_path):
    inner=Inner();m=module()
    route=m.CompileRouteServices(inner,tmp_path,'route',('TEST-A',),'actual compiler facts',lambda:None)
    r=route.step('red','v62-step4-red')
    assert r.next_stage=='prepare' and r.result is None and inner.count==2
    assert route.reconcile('red','v62-step4-red')==r and inner.count==2
    assert route.step('prepare','v62-step5-prepare').next_stage=='red'
    assert inner.delegated==[('prepare','v62-step5-prepare')]
    assert not (tmp_path/'.agent/runs/monopoly-game-lobby/result.json').exists()


def test_frozen_tests_block_the_route_before_counter_change(tmp_path):
    inner=Inner();inner.tdd.frozen=True
    route=module().CompileRouteServices(inner,tmp_path,'route',('TEST-A',),'facts',lambda:None)
    with pytest.raises(ValueError):route.step('red','op')
    assert inner.count==1
