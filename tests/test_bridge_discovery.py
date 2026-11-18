"""Live health regression: discover through an explicit read-only capability command."""
import json
import pytest
from test_unity_transport import bridge, publish
from unity_coder.adapters.unity.transport import BridgeTransport

@pytest.mark.parametrize('valid', [True, False])
def test_empty_health_requires_verified_main_thread_capabilities(bridge, valid):
    fake, _, req = bridge
    fake.commands = []
    def http(port, method, path, body, timeout):
        if path == '/resource/project_info':
            fake.calls.append((port, method, path, body))
            return {'status':'success','data':json.dumps({'unityVersion':'2022.3.62t10'})}
        if body and body.get('command') == 'FrameworkVerifyCapabilities':
            fake.calls.append((port, method, path, body))
            return {'status':'success','data':json.dumps({'protocol':1 if valid else 99,'command':'FrameworkVerify','modes':['compile','tests']})}
        return fake.http(port, method, path, body, timeout)
    fake.on_wait = lambda: publish(fake, req)
    worker = BridgeTransport(fake.root, ports=(59183,), http=http, clock=fake.clock, pause=fake.wait, timeout=2)
    result = worker.run_tests(req)
    if valid:
        assert result.tests.passed == ('Test',)
    else:
        assert result.tests.operational_error
        assert not any(c[3] and c[3].get('command') == 'FrameworkVerify' for c in fake.calls)
