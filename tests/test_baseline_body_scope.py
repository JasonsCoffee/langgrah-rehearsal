"""Actual error cases, rather than all failed assertions, determine repair scope."""
import importlib.util
from pathlib import Path
import pytest


def helper():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/baseline_body_scope.py')
    s=importlib.util.spec_from_file_location('baseline_body_scope',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def inputs():
    raw={'mode':'tests','request':{'full_suite':True,'test_selection':['A','B']},
        'executed':['A','B'],'passed':[],'failed':['A','B'],'skipped':[],'inconclusive':[],
        'failure_details':[{'test':'A','state':'Failed:Failure','site':'Test','message':'Expected business behavior'},
            {'test':'B','state':'Failed:Error','site':'Test','message':'System.NullReferenceException'}]}
    c={'units':[{'id':'ASSERT','role':'test','status':'active'},{'id':'ERROR','role':'test','status':'active'}],
        'test_links':[{'test_id':'A','author_unit':'ASSERT'},{'test_id':'B','author_unit':'ERROR'}]}
    return raw,c


def test_only_real_body_error_author_is_revised():
    r,c=inputs();assert helper().body_error_scope(r,c)=={'ERROR':['B']}


@pytest.mark.parametrize('bad',['setup','missing','unknown-error','unexpected-selection','disabled','impl'])
def test_ambiguous_or_non_body_failures_need_separate_diagnosis(bad):
    r,c=inputs()
    if bad=='setup':r['failure_details'][1]['site']='SetUp'
    elif bad=='missing':r['failure_details']=[]
    elif bad=='unknown-error':r['failure_details'][1]['message']='Unknown native crash'
    elif bad=='unexpected-selection':r['executed'].append('C')
    elif bad=='disabled':r['skipped']=['A']
    else:c['units'][1]['role']='impl'
    with pytest.raises(ValueError):helper().body_error_scope(r,c)
