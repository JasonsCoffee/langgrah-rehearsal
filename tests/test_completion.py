"""Accepted metadata commits must descend from exactly the reviewed source tree."""
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from unity_coder.core.completion import CandidateCompletion
from unity_coder.core.constraints import LearnedConstraint
from unity_coder.core.review import ReviewGate
from unity_coder.core.lifecycle import RunLifecycle
from unity_coder.core.verification import VerificationRequest, VerificationResult
from unity_coder.core.evidence import TestResult as Evidence


def prepare(workspace, tmp_path, accept=True):
    manager, repo, base, contract = workspace
    integration = manager.create_integration(1, base)
    request = VerificationRequest('r1','run1',1,contract.sha256,base,'art','profile','env',('Test',),True)
    result = VerificationResult(request,'tests','passed',test_result=Evidence(('Test',),('Test',),('Test',),()),
                                full_suite_verified=True,behavioral=True)
    review = ReviewGate(RunLifecycle(tmp_path/'state','run1',contract_version=1,contract_sha256=contract.sha256),
                        authenticate_human=lambda token:'human' if token=='human' else None)
    files={p:(integration.path/p).read_bytes() for p in git(integration.path,'ls-files').splitlines()}
    review.offer(result,files,evidence_refs=('evidence/tests.json',))
    if accept: review.decide('human',request,'accept',findings=())
    completion=CandidateCompletion(manager,integration,review)
    entries=(LearnedConstraint('Preserve identity',1,'R1','evidence/tests.json'),)
    return completion,request,entries,integration,repo,base


def test_metadata_commit_has_exact_parent_and_only_managed_file(workspace,tmp_path):
    c,r,e,w,repo,base=prepare(workspace,tmp_path)
    result=c.complete(r,e)
    tip=result['candidate_revision']
    assert result['outcome']=='pass'
    assert git(w.path,'rev-parse',tip+'^')==base
    assert git(w.path,'diff','--name-only',base,tip)=='AGENTS.md'
    assert 'Preserve identity' in (w.path/'AGENTS.md').read_text()
    assert git(repo,'rev-parse','HEAD')==base
    assert c.complete(r,e)==result


def test_pending_review_cannot_create_commit(workspace,tmp_path):
    c,r,e,w,repo,base=prepare(workspace,tmp_path,False)
    with pytest.raises(ValueError): c.complete(r,e)
    assert git(w.path,'rev-parse','HEAD')==base
    assert not (w.path/'AGENTS.md').exists()


def test_unreviewed_source_edit_blocks_completion(workspace,tmp_path):
    c,r,e,w,repo,base=prepare(workspace,tmp_path)
    (w.path/'unexpected.txt').write_bytes(b'unreviewed')
    with pytest.raises(ValueError): c.complete(r,e)
    assert git(w.path,'rev-parse','HEAD')==base
    assert (w.path/'unexpected.txt').read_bytes()==b'unreviewed'


def test_crash_after_ref_publication_reconciles_same_commit(workspace,tmp_path,monkeypatch):
    c,r,e,w,repo,base=prepare(workspace,tmp_path)
    original=c._publish
    def interrupted(before,after):
        original(before,after)
        raise OSError('crash after compare-and-swap')
    monkeypatch.setattr(c,'_publish',interrupted)
    with pytest.raises(OSError): c.complete(r,e)
    tip=git(w.path,'rev-parse','HEAD')
    assert tip!=base
    resumed=CandidateCompletion(c.manager,w,c.review)
    assert resumed.complete(r,e)['candidate_revision']==tip
    assert git(w.path,'rev-list','--count',base+'..HEAD')=='1'
