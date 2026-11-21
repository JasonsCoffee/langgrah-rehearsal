"""Readiness races permit bounded retries only before any test submission."""
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from unity_coder.core.evidence import TestResult as Result
from unity_coder.core.verification import VerificationRequest,WorkerEvidence


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/lobby_readiness_wait.py')
    spec=importlib.util.spec_from_file_location('lobby_readiness_wait',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def fixture(tmp_path,error='No exact-project Bridge with FrameworkVerify tooling'):
    request=VerificationRequest('verify','run',69,'contract','candidate','presentation','profile','env',('T',),True)
    calls=[];bad=WorkerEvidence(request,tests=Result((),(),(),(),operational_error=error))
    good=WorkerEvidence(request,tests=Result(('T',),('T',),(),('T',)))
    def execute(req):calls.append(req);return bad if len(calls)==1 else good
    inner=SimpleNamespace(root=tmp_path,run_tests=execute)
    return request,inner,calls,bad,good


def test_transient_readiness_wait_preserves_request_and_actual_assertion_result(tmp_path):
    m=module();req,inner,calls,bad,good=fixture(tmp_path);ready=[];pauses=[];records=[]
    def check():
        ready.append(True)
        if len(ready)==1:raise ValueError('Verified host is still reloading')
    result=m.ReadinessWaitTransport(inner,ready=check,record=records.append,pause=pauses.append).run_tests(req)
    assert result==good and calls==[req,req] and len(ready)==2 and pauses==[1]
    assert len(records)==1 and records[0]['zero_submission'] is True


def test_persistent_unavailability_stops_after_three_readiness_checks(tmp_path):
    m=module();req,inner,calls,bad,good=fixture(tmp_path);ready=[]
    def check():ready.append(True);raise OSError('busy')
    result=m.ReadinessWaitTransport(inner,ready=check,record=lambda _:None,pause=lambda _:None).run_tests(req)
    assert result==bad and calls==[req] and len(ready)==3


def test_repeated_zero_submission_failures_have_a_fixed_bound(tmp_path):
    m=module();req,inner,calls,bad,good=fixture(tmp_path)
    def execute(request):calls.append(request);return bad
    inner.run_tests=execute
    assert m.ReadinessWaitTransport(inner,ready=lambda:None,record=lambda _:None,pause=lambda _:None).run_tests(req)==bad
    assert calls==[req]*4


def test_intent_appearing_during_readiness_forbids_retry(tmp_path):
    m=module();req,inner,calls,bad,good=fixture(tmp_path)
    def check():
        folder=m.ticket_path(tmp_path,req);folder.mkdir(parents=True);(folder/'request.json').write_text('{}')
    assert m.ReadinessWaitTransport(inner,ready=check,record=lambda _:None,pause=lambda _:None).run_tests(req)==bad
    assert calls==[req]


def test_ambiguous_transport_failure_is_not_retried(tmp_path):
    m=module();req,inner,calls,bad,good=fixture(tmp_path,'Verification timed out; reconcile before retry')
    assert m.ReadinessWaitTransport(inner,ready=lambda:None,record=lambda _:None,pause=lambda _:None).run_tests(req)==bad
    assert calls==[req]


def recovery():
    m=module();wire={'request_id':'v69-step9-verify','candidate_revision':m.CANDIDATE,
        'contract_version':69,'contract_sha256':m.CONTRACT}
    result={'outcome':'operational','contract_version':69,'contract_sha256':m.CONTRACT,
        'candidate_revision':m.CANDIDATE}
    evidence={'request':wire,'gate':'tests','status':'operational','test_result':None,
        'violations':[{'message':m.DISCOVERY_ERROR}]}
    transaction={'operation':'v69-step9-verify','stage':'verify','complete':True}
    compiled={'request':wire,'mode':'compile','status':'completed','passed':True,'violations':[]}
    return m,result,evidence,transaction,compiled


def test_only_the_actual_compiled_zero_submission_stop_is_recoverable():
    m,result,evidence,transaction,compiled=recovery()
    m.validate_stop(result,evidence,transaction,compiled,submitted=False)


@pytest.mark.parametrize('change',['candidate','compiled','submitted','incomplete','other_error'])
def test_inconsistent_or_submitted_recovery_is_rejected(change):
    m,result,evidence,transaction,compiled=recovery();submitted=False
    if change=='candidate':result['candidate_revision']='other'
    if change=='compiled':compiled['passed']=False
    if change=='submitted':submitted=True
    if change=='incomplete':transaction['complete']=False
    if change=='other_error':evidence['violations'][0]['message']='Unknown callback timeout'
    with pytest.raises(ValueError):m.validate_stop(result,evidence,transaction,compiled,submitted=submitted)
