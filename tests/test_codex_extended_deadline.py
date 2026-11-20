"""Explicit longer production waits preserve safe defaults and diagnostics."""
import importlib.util
from pathlib import Path
from time import monotonic
import pytest
from unity_coder.core.ai_models import ModelError
from unity_coder.core.codex_stdio import CodexStdioExchange, StdioRpc


def test_expired_rpc_has_explicit_non_billing_diagnostics():
    rpc=StdioRpc.__new__(StdioRpc);rpc.deadline=monotonic()-1
    with pytest.raises(ModelError) as failure:rpc._next()
    assert failure.value.diagnostics=={'transport':'codex_stdio','failure_kind':'deadline'}


def test_longer_allowance_requires_explicit_trusted_constructor():
    extended=CodexStdioExchange(disabled_mcp=(),max_timeout_seconds=600)
    assert extended.max_timeout_seconds==600
    assert CodexStdioExchange(disabled_mcp=()).max_timeout_seconds==180


@pytest.mark.parametrize('bad',[0,601,True])
def test_even_explicit_allowance_is_bounded(bad):
    with pytest.raises(ValueError):CodexStdioExchange(disabled_mcp=(),max_timeout_seconds=bad)


def test_recovery_production_bound_is_explicit():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/codex_lobby.py')
    s=importlib.util.spec_from_file_location('codex_lobby_long',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    assert m.EXTENDED_PRODUCTION_TIMEOUT_SECONDS==600
