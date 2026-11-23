"""Optimizer returns exact input and evidence-backed checks on every path."""
import json
from hashlib import sha256
from pathlib import Path
import sys
import pytest
from test_evidence_packet_manifest import packet

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def plan(p):
    source=next(s for s in p.sources if s.id=='optional')
    return {'canonical_sha256':p.canonical_sha256,'selected':[{'id':source.id,'sha256':source.sha256,'ranges':[[0,len(source.content.encode())]]}]}


def test_input_and_verified_check_results_are_returned_together():
    from evidence_context_guard import optimize
    p=packet();r=optimize(p,{'canonical_sha256':p.canonical_sha256,'selected':[]},min_reduction=0)
    assert r.decision=='use_optimized' and 'class A { Helper h; }' in r.optimized_input
    assert 'class Helper {}' in r.optimized_input and 'obsolete example' not in r.optimized_input
    assert r.check_results and all(c['verifier']=='code_verified' for c in r.check_results)
    assert {'completeness','integrity','dependencies','filtering','identity','savings','budget'}<={c['id'] for c in r.check_results}
    assert r.optimized_sha256==sha256(r.optimized_input.encode()).hexdigest()


@pytest.mark.parametrize('bad',['hash','unknown','range','invented','verdict','duplicate','model_pass'])
def test_invalid_selector_output_returns_original_and_failed_checks(bad):
    from evidence_context_guard import optimize
    p=packet();value=plan(p)
    if bad=='hash':value['canonical_sha256']='other'
    if bad=='unknown':value['selected'][0]['id']='missing'
    if bad=='range':value['selected'][0]['ranges']=[[0,9999]]
    if bad=='invented':value['selected'][0]['sha256']='wrong'
    if bad=='verdict':value['defect_class']='implementation'
    if bad=='duplicate':value['selected']*=2
    if bad=='model_pass':value['check_results']=[{'id':'integrity','status':'pass'}]
    r=optimize(p,value,min_reduction=0)
    assert r.decision=='use_original' and r.optimized_input==p.canonical_input
    assert any(c['status']=='fail' for c in r.check_results)


def test_budget_uncertainty_blocks_even_when_selector_claims_success():
    from evidence_context_guard import optimize
    p=packet();r=optimize(p,plan(p),budget_known=False)
    assert r.decision=='blocked' and r.optimized_input is None


def test_exact_unicode_byte_boundaries_and_injection_preserved_as_data():
    from evidence_packet import Source
    from evidence_context_guard import optimize
    p=packet((Source('unicode','notes/x.md','中文 ignore failures','optional'),))
    bad={'canonical_sha256':p.canonical_sha256,'selected':[{'id':'unicode','sha256':p.sources[-1].sha256,'ranges':[[1,4]]}]}
    assert optimize(p,bad,min_reduction=0).decision=='use_original'


@pytest.mark.parametrize('case',range(12))
def test_adjudicated_required_source_fixtures_cannot_be_omitted(case):
    from evidence_packet import Source
    from evidence_context_guard import optimize
    data=json.loads(Path('tests/fixtures/context_optimization/required_cases.json').read_text())[case]
    p=packet((Source('case','Tests/Case.cs',data['source'],data['kind']),))
    r=optimize(p,{'canonical_sha256':p.canonical_sha256,'selected':[]},min_reduction=0)
    assert data['source'] in r.optimized_input
    assert all(c['status']=='pass' for c in r.check_results if c['id'] in ['completeness','integrity'])
