"""Codex session bounds are separate from the unchanged HTTP client limit."""
import pytest
from unity_coder.core.ai_models import ModelClient, ModelConfig
from unity_coder.core.codex_backend import CodexModelClient, CodexPolicy


def test_codex_session_can_wait_longer_without_changing_http_bound(tmp_path):
    work=tmp_path/'worker';work.mkdir()
    p=CodexPolicy('coder','gpt-6.2-sol','low','dispatch_accounting','approval.json')
    c=CodexModelClient(p,tmp_path/'state',work,exchange=lambda _:(),authorize=lambda _:True,
        timeout=180,session_timeout=600)
    assert c.timeout==180 and c.session_timeout==600
    with pytest.raises(ValueError):ModelClient(ModelConfig('coder','openrouter','test',''),timeout=600)


@pytest.mark.parametrize('bad',[0,601,True])
def test_codex_session_allowance_is_bounded(tmp_path,bad):
    p=CodexPolicy('coder','model','low')
    with pytest.raises(ValueError):CodexModelClient(p,tmp_path/'state',tmp_path,
        exchange=lambda _:(),authorize=lambda _:True,session_timeout=bad)
