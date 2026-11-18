"""Assertion Red must never be inferred from setup/runner failure status."""
import json
from pathlib import Path

import pytest

from test_unity_transport import bridge, publish
from unity_coder.core.tdd import BehaviorEvidence, validate_behavior


def failed_reply(fake, req, details):
    publish(fake,req)
    for path in fake.root.glob('.agent/verification/*/result.json'):
        raw=json.loads(path.read_text())
        raw.update(passed=[],failed=['Test'],failure_details=details)
        path.write_text(json.dumps(raw))


@pytest.mark.parametrize('state,site', [('Failed:Error','Test'),('Failed','SetUp'),('Failed','Parent'),('Failed','TearDown')])
def test_setup_and_runner_errors_are_not_behavioral_red(bridge,state,site):
    fake,factory,req=bridge
    fake.on_wait=lambda:failed_reply(fake,req,[{'test':'Test','state':state,'site':site,'message':'fixture failure'}])
    result=factory().run_tests(req).tests
    with pytest.raises(ValueError,match='Nonbehavioral'):
        validate_behavior(BehaviorEvidence('snapshot',('Test',),result),('Test',))


def test_assertion_diagnostic_reaches_behavioral_evidence(bridge):
    fake,factory,req=bridge
    fake.on_wait=lambda:failed_reply(fake,req,[{'test':'Test','state':'Failed','site':'Test','message':'Expected 2 but was 0'}])
    result=factory().run_tests(req).tests
    validate_behavior(BehaviorEvidence('snapshot',('Test',),result),('Test',))
    assert any('Expected 2 but was 0' in message for message in result.messages)


def test_failed_legacy_callback_cannot_assume_assertion_red(bridge):
    fake,factory,req=bridge
    fake.on_wait=lambda:failed_reply(fake,req,[])
    assert factory().run_tests(req).tests.operational_error


def test_suite_teardown_failure_cannot_pass_when_all_leaves_pass(bridge):
    fake,factory,req=bridge
    def callback():
        publish(fake,req)
        for path in fake.root.glob('.agent/verification/*/result.json'):
            raw=json.loads(path.read_text())
            raw['suite_errors']=['Fixture: teardown failure']
            path.write_text(json.dumps(raw))
    fake.on_wait=callback
    result=factory().run_tests(req).tests
    with pytest.raises(ValueError,match='Nonbehavioral'):
        validate_behavior(BehaviorEvidence('snapshot',('Test',),result),('Test',))
