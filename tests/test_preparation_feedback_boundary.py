"""Frozen setup feedback cannot leak into subsequent implementation calls."""
from test_contracts import bundle
from test_workspaces import workspace
from test_local_executor import local
from unity_coder.core.evidence import TestResult as Evidence
from unity_coder.core.local_executor import WorkerPatch
from unity_coder.core.verification import VerificationResult


def test_setup_feedback_is_cleared_only_after_valid_baseline(local):
    executor,services,workers,_,_,_=local
    verifier=services.verifier
    def invalid(request,root,patches):
        tests=Evidence(request.test_selection,request.test_selection,(),request.test_selection,
            failure_kind='setup',messages=('Fixture lifecycle failed',))
        return VerificationResult(request,'tests','failed',test_result=tests)
    services.verifier=invalid
    executor.advance('prepare');executor.advance('red')
    assert 'Fixture lifecycle failed' in services.state['feedback']
    feedback=[]
    def author(unit,stage,files,message,operation):
        feedback.append((stage,message))
        return WorkerPatch({},'retained fixture source')
    workers.code=author
    executor.advance('prepare')
    assert feedback == [('test_authoring','Baseline test setup requires repair: Fixture lifecycle failed')]
    services.verifier=verifier
    executor.advance('red')
    assert services.tdd.frozen
    executor.advance('code')
    assert all(message=='' for stage,message in feedback if stage=='green')
