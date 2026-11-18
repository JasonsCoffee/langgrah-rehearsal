"""Invalid baseline setup is bounded test preparation, not implementation Red."""
from test_contracts import bundle
from test_workspaces import workspace
from test_local_executor import local
from unity_coder.core.evidence import TestResult as Evidence, Violation
from unity_coder.core.verification import VerificationResult


def test_invalid_setup_returns_to_test_author_without_impl_attempt(local):
    executor,services,workers,_,_,_=local
    original=services.verifier
    def invalid(request,root,patches):
        tests=Evidence(request.test_selection,request.test_selection,(),request.test_selection,
                       failure_kind='setup',messages=('Test fixture setup failed',))
        return VerificationResult(request,'tests','failed',test_result=tests,
            violations=(Violation('test_evidence','','','Nonbehavioral setup'),))
    services.verifier=invalid
    executor.advance('prepare')
    result=executor.advance('red')
    assert result.next_stage=='prepare'
    assert not services.tdd.frozen
    author=next(u for u in services.contract.units if u.role=='test')
    assert services.tdd.state(author.id).preparation_attempts==1
    assert all(services.retry.state(u.id).failed_attempts==0 for u in services.contract.units)
    assert 'setup' in services.state['feedback'].lower()


def test_invalid_setup_exhausts_preparation_without_freezing(local):
    executor,services,workers,_,_,_=local
    author=next(u for u in services.contract.units if u.role=='test')
    for _ in range(2):services.tdd.record_preparation_failure(author.id)
    # Existing authored files are independently reviewed; avoid a synthetic model call.
    services.tdd.approve_tests(author.id,'Coverage reviewed')
    executor.budget.begin_cycle(1,services.contract.sha256,
        {u.id:services.contract.lineage_for(u.id) for u in services.contract.units})
    def invalid(request,root,patches):
        return VerificationResult(request,'tests','failed',
            test_result=Evidence(request.test_selection,request.test_selection,(),request.test_selection,
                                 failure_kind='setup',messages=('Bad fixture',)))
    services.verifier=invalid
    result=services.step('red','invalid-baseline')
    assert result.result['outcome']=='rework'
    assert not services.tdd.frozen
    assert services.tdd.state(author.id).stage=='preparation_exhausted'
