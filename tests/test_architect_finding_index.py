"""Exact original Judge authority survives compact Architect delivery."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_handoff_keeps_exact_explanation_and_every_unresolved_finding():
    from architect_finding_index import finding_index
    items=[{'unit':'U','criterion':'C','classification':'implementation','explanation':'Keep this exact uncertainty.',
        'evidence':['receipt'],'resolved':False,'retry':'STALLED'}]
    result=finding_index('candidate','contract',items,[10,20],{'receipt':'exact original'})
    assert result['findings']==items and result['budget']==[10,20]
    assert result['sources']=={'receipt':'exact original'}


def test_unresolved_missing_reference_is_an_error():
    from architect_finding_index import finding_index
    with pytest.raises(ValueError):finding_index('c','h',[{'unit':'U','classification':'contract','explanation':'x','evidence':['absent'],'resolved':False}],[0,0],{})


def test_total_cost_includes_selector_and_expansion_overhead():
    from context_cost_report import cost_report
    r=cost_report(canonical_input=1000,delivered_input=500,selector_input=900,selector_output=100,
        judge_output=50,extra_judge_input=100,judge_input_rate=10,judge_output_rate=20,
        selector_input_rate=1,selector_output_rate=2)
    assert r['optimized_cost']==pytest.approx((600*10+50*20+900+200)/1000000)
    assert r['input_reduction']==.5
    r=cost_report(canonical_input=1000,delivered_input=500,judge_input_rate=None)
    assert r['monetary_savings_verified'] is False and r['optimized_cost'] is None
