"""Production status, candidate review guidance and accepted constraint delivery."""
from dataclasses import replace
import json
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from test_local_executor import local, run
from test_production_effect_recovery import Crash, reopen
from unity_coder.core.local_executor import TestReviewRejected, _verification
from unity_coder.core.constraints import LearnedConstraint, read_constraints
from unity_coder.core.completion import CandidateCompletion


def test_attempt_counts_survive_stage_exit_cancellation_and_reconnect(local):
    executor,services,workers,_,_,_=local
    def reject(*args):raise TestReviewRejected('Missing assertion')
    workers.review_tests=reject
    executor.advance('prepare')
    assert executor.progress.status()['attempts']['U0-tests']==1
    executor.request_cancel()
    executor.advance('prepare')
    assert executor.outcome()=='cancelled'
    reopen(executor,services)
    assert executor.progress.status()['attempts']['U0-tests']==1


def test_production_review_guidance_is_persisted_and_bound_to_candidate(local):
    executor,services,_,_,_,review=local
    assert run(executor)['outcome']=='awaiting_human_review'
    record=review.state()
    package=record['package']
    assert package['request']==record['request']
    assert package['launch_instructions'] and package['required_interactions']
    assert 'visual_references' in package and package['placeholder_limitations']
    assert package['scope']=='code'
    reopen(executor,services)
    assert review.state()['package']==package


def test_visual_guidance_reaches_review_and_cannot_change_under_same_request(local):
    from unity_coder.core.review import ReviewPackage
    executor,services,_,_,_,review=local
    def package(request):
        return ReviewPackage(request,'visual',(services.contract.spec.path,),
            'Launch the declared entry',('Preview then reset',),
            (services.contract.spec.path,),'Temporary review artwork')
    services.review_package=package
    run(executor)
    assert review.state()['package']['required_interactions']==['Preview then reset']
    evidence=_verification(services.state['verification'])
    with pytest.raises(ValueError):
        review.offer(evidence,services._files(),evidence_refs=(services.state['evidence_ref'],),
                     package=replace(package(evidence.request),launch_instructions='Changed instructions'))


@pytest.mark.parametrize('invalid',['stale','missing','escape'])
def test_review_gate_rejects_stale_or_incomplete_guidance(local,invalid):
    from unity_coder.core.review import ReviewPackage
    executor,services,_,_,_,review=local
    run(executor)
    evidence=_verification(services.state['verification'])
    request=evidence.request
    package=ReviewPackage(request,'visual',('scene.unity',),'Open scene',('Click preview',),
                          ('reference.png',),'Placeholder art only')
    if invalid=='stale':package=replace(package,request=replace(request,candidate_revision='old'))
    if invalid=='missing':package=replace(package,required_interactions=())
    if invalid=='escape':package=replace(package,visual_references=('../reference.png',))
    with pytest.raises(ValueError):
        review.offer(evidence,services._files(),evidence_refs=(services.state['evidence_ref'],),package=package)


def accept(local):
    executor,services,_,_,_,review=local
    run(executor)
    request=_verification(services.state['verification']).request
    review.decide('credential',request,'accept',findings=())
    entries=(LearnedConstraint('Preserve the verified identity',1,'R7',services.state['evidence_ref']),)
    return executor,services,request,entries


def test_accepted_constraints_flush_through_graph_after_reconnect(local):
    executor,services,request,entries=accept(local)
    services.confirm_constraints(request,entries)
    services.confirm_constraints(request,entries)
    services=reopen(executor,services)
    executor.resume_review()
    assert run(executor)['outcome']=='pass'
    active,archive=read_constraints((services.integration.path/'AGENTS.md').read_bytes())
    assert len(active)==1 and not archive
    assert active[0]['statement']==entries[0].statement
    assert active[0]['provenance'][0]['candidate_revision']==request.candidate_revision


def test_confirmed_constraints_cannot_be_replaced_or_forged(local):
    executor,services,request,entries=accept(local)
    with pytest.raises(ValueError):services.confirm_constraints(replace(request,candidate_revision='old'),entries)
    with pytest.raises(ValueError):services.confirm_constraints(request,(replace(entries[0],evidence_ref='unknown.json'),))
    services.confirm_constraints(request,entries)
    with pytest.raises(ValueError):services.confirm_constraints(request,(replace(entries[0],statement='Different'),))


def test_pending_human_review_cannot_confirm_constraints(local):
    executor,services,_,_,_,_=local
    run(executor)
    request=_verification(services.state['verification']).request
    entries=(LearnedConstraint('Preserve identity',1,'R7',services.state['evidence_ref']),)
    with pytest.raises(ValueError):services.confirm_constraints(request,entries)


def test_nonempty_constraint_completion_recovers_same_commit(local,monkeypatch):
    executor,services,request,entries=accept(local)
    services.confirm_constraints(request,entries)
    executor.resume_review()
    publish=CandidateCompletion._publish
    def crash(self,before,after):
        publish(self,before,after)
        raise Crash()
    monkeypatch.setattr(CandidateCompletion,'_publish',crash)
    with pytest.raises(Crash):executor.advance('finalize')
    head=git(services.integration.path,'rev-parse','HEAD')
    monkeypatch.setattr(CandidateCompletion,'_publish',publish)
    services=reopen(executor,services)
    assert run(executor)['outcome']=='pass'
    assert git(services.integration.path,'rev-parse','HEAD')==head
    active,_=read_constraints((services.integration.path/'AGENTS.md').read_bytes())
    assert len(active)==1 and len(active[0]['provenance'])==1
