"""Live rollout keeps a bounded, persistent independent canonical comparison."""
from pathlib import Path
import sys
import pytest
from test_evidence_packet_manifest import packet

sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_live_audit_preserves_exact_authority_and_records_coverage(tmp_path):
    from live_context_audit import LiveReviewAudit
    from evidence_context_guard import optimize
    p=packet();result=optimize(p,{'canonical_sha256':p.canonical_sha256,'selected':[]},min_reduction=0)
    expected={'defect_class':'implementation','explanation':'exact authoritative finding'}
    calls=[]
    def shadow():
        calls.append('canonical')
        return {'defect_class':'implementation','explanation':'Independent equivalent routing'}
    audit=LiveReviewAudit(tmp_path)
    assert audit.observe('op','defect:tests',p,result,expected,shadow)==expected
    row=audit.read()['reviews'][0]
    assert calls==['canonical'] and row['check_results']==list(result.check_results)
    assert row['canonical_sha256']==p.canonical_sha256 and row['audit']['routing_agrees']
    assert audit.observe('op','defect:tests',p,result,expected,shadow)==expected
    assert len(calls)==1


def test_routing_disagreement_disables_class_and_stops(tmp_path):
    from live_context_audit import LiveReviewAudit
    from evidence_context_guard import optimize
    from unity_coder.core.ai_models import ModelError
    p=packet();r=optimize(p,{'canonical_sha256':p.canonical_sha256,'selected':[]},min_reduction=0)
    audit=LiveReviewAudit(tmp_path)
    with pytest.raises(ModelError,match='disagree'):
        audit.observe('op','defect:tests',p,r,{'defect_class':'implementation','explanation':'a'},
            lambda:{'defect_class':'contract','explanation':'b'})
    assert 'defect:tests' in audit.read()['disabled_classes']


def test_uncertain_shadow_is_not_replayed_under_another_operation(tmp_path):
    from live_context_audit import LiveReviewAudit
    from evidence_context_guard import optimize
    from unity_coder.core.ai_models import ModelError
    p=packet();r=optimize(p,{'canonical_sha256':p.canonical_sha256,'selected':[]},min_reduction=0)
    def broken():raise ModelError('uncertain shadow submission')
    a=LiveReviewAudit(tmp_path)
    with pytest.raises(ModelError):a.observe('op','defect:tests',p,r,{'defect_class':'contract'},broken)
    with pytest.raises(ModelError,match='reconcil'):
        LiveReviewAudit(tmp_path).observe('new-op','defect:tests',p,r,{'defect_class':'contract'},lambda:pytest.fail('replayed'))


def test_envelope_unavailable_requires_deterministic_mode(tmp_path):
    from live_context_audit import LiveReviewAudit
    a=LiveReviewAudit(tmp_path)
    assert not a.selection_allowed('defect:tests',audit_fits=False)
    assert a.selection_allowed('defect:tests',audit_fits=True)


def test_mixed_runtime_classification_is_distinct():
    from live_context_audit import packet_class
    assert packet_class('defect',{'gate':'tests','behavioral':False})=='defect:mixed'
    assert packet_class('defect',{'gate':'tests','behavioral':True})=='defect:tests'
    assert packet_class('test_review',{'gate':'source'})=='test_review:source'
