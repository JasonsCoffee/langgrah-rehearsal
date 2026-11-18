"""Bounded in-request recovery when compilation temporarily blocks the Bridge."""
import pytest
from test_unity_transport import bridge, publish
from unity_coder.adapters.unity.transport import BridgeTransport

@pytest.mark.parametrize('lost', ['poll', 'submission'])
def test_temporary_disconnect_reconciles_without_duplicate_submission(bridge, lost):
    fake, _, req = bridge
    sent = False
    raised = False
    def http(port, method, path, body, timeout):
        nonlocal sent, raised
        result = fake.http(port, method, path, body, timeout)
        if path == '/execute':
            sent = True
            if lost == 'submission' and not raised:
                raised = True
                raise TimeoutError('accepted, then disconnected')
        if path == '/' and sent and lost == 'poll' and not raised:
            raised = True
            raise TimeoutError('domain reload')
        return result
    fake.on_wait = lambda: publish(fake, req)
    worker=BridgeTransport(fake.root,ports=(59183,),http=http,clock=fake.clock,pause=fake.wait,timeout=2)
    assert worker.run_tests(req).tests.passed == ('Test',)
    assert sum(c[2] == '/execute' for c in fake.calls) == 1
