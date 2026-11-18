"""Frozen pre-submission discovery recovery between compile and tests."""

import json
import pytest
from test_unity_transport import bridge, publish
from unity_coder.adapters.unity.transport import BridgeTransport


@pytest.mark.parametrize("recovers",[True,False])
def test_verified_project_main_thread_discovery_waits_through_reload(bridge,recovers):
    fake,_,request=bridge
    fake.commands=[]
    attempts=[]
    def http(port,method,path,body,timeout):
        if path=="/resource/project_info":
            attempts.append(1)
            if not recovers or len(attempts)==1:
                raise TimeoutError("Domain reload")
            return {"status":"success","data":json.dumps({"unityVersion":"fixture"})}
        if body and body.get("command")=="FrameworkVerifyCapabilities":
            return {"status":"success","data":json.dumps({"protocol":1,"command":"FrameworkVerify","modes":["compile","tests"],"ready":True})}
        return fake.http(port,method,path,body,timeout)
    fake.on_wait=lambda:publish(fake,request)
    worker=BridgeTransport(fake.root,ports=(59183,),http=http,clock=fake.clock,pause=fake.wait,timeout=2)
    result=worker.run_tests(request)
    submitted=[c for c in fake.calls if c[3] and c[3].get("command")=="FrameworkVerify"]
    if recovers:
        assert result.tests.passed==("Test",)
        assert len(submitted)==1
    else:
        assert result.tests.operational_error
        assert not submitted and fake.ticks==2
