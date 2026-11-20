"""Frozen rejected-event cleanup: an active stream must close immediately."""
import pytest
from unity_coder.core.ai_models import ModelError
from unity_coder.core.codex_backend import CodexModelClient,CodexPolicy


def test_rejected_tool_event_closes_retained_transport_generator(tmp_path):
    closed=[]
    def events():
        try:
            yield {'method':'item/started','params':{'item':{'type':'commandExecution'}}}
            pytest.fail('must not continue after a forbidden tool event')
        finally:closed.append(True)
    stream=events()
    work=tmp_path/'worker';work.mkdir()
    policy=CodexPolicy('coder','model','low','dispatch_accounting','approvals/explicit.json')
    client=CodexModelClient(policy,tmp_path/'state',work,exchange=lambda req:stream,authorize=lambda _:True)
    try:
        with pytest.raises(ModelError,match='tool'):client.generate_operation('call','contract',max_output_tokens=64)
        assert closed==[True]
    finally:stream.close()
