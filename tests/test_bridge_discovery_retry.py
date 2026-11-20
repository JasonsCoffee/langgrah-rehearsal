"""Only an exact pre-submission discovery failure may be retried by the host."""
from dataclasses import asdict
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unity_coder.core.evidence import TestResult as Result
from unity_coder.core.verification import VerificationRequest,WorkerEvidence


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/bridge_discovery_retry.py')
    s=importlib.util.spec_from_file_location('bridge_discovery_retry',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def setup(tmp_path,error='No exact-project Bridge with FrameworkVerify tooling'):
    req=VerificationRequest('red','run',64,'contract','candidate','presentation','profile','env',('T',),True)
    calls=[]
    bad=WorkerEvidence(req,tests=Result((),(),(),(),operational_error=error))
    good=WorkerEvidence(req,tests=Result(('T',),('T',),(),('T',)))
    def execute(request):calls.append(request);return bad if len(calls)==1 else good
    return req,SimpleNamespace(root=tmp_path,run_tests=execute),calls


def test_zero_submission_retry_keeps_exact_request_and_actual_result(tmp_path):
    req,inner,calls=setup(tmp_path);ready=[];records=[]
    wrapper=module().DiscoveryRetryTransport(inner,ready=lambda:ready.append(True),record=records.append)
    result=wrapper.run_tests(req)
    assert result.tests.failed==('T',) and calls==[req,req] and ready==[True] and len(records)==1


def test_a_durable_intent_prevents_resubmission(tmp_path):
    req,inner,calls=setup(tmp_path)
    ticket=sha256(json.dumps({'request':asdict(req),'mode':'tests'},sort_keys=True).encode()).hexdigest()
    p=tmp_path/'.agent/verification'/ticket/'request.json';p.parent.mkdir(parents=True);p.write_text('{}')
    result=module().DiscoveryRetryTransport(inner,ready=lambda:None,record=lambda _:None).run_tests(req)
    assert result.tests.operational_error and calls==[req]


def test_other_transport_errors_are_never_retried(tmp_path):
    req,inner,calls=setup(tmp_path,'Verification timed out; retain intent and reconcile before retry')
    result=module().DiscoveryRetryTransport(inner,ready=lambda:None,record=lambda _:None).run_tests(req)
    assert result.tests.operational_error and calls==[req]
