"""Caller diagnostics preserve error identity and never retain secret payloads."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from unity_coder.core.ai_models import ModelError


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/codex_error_capture.py')
    spec=importlib.util.spec_from_file_location('codex_error_capture',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def calls(tmp_path,invoke):
    return SimpleNamespace(budget=SimpleNamespace(root=tmp_path),generate=invoke,
        client=SimpleNamespace(config=SimpleNamespace(provider='codex',role='judge',model='gpt-6.1-sol',effort='medium')))


def test_static_protocol_failure_is_captured_and_original_error_reraised(tmp_path):
    error=ModelError('Codex RPC stream ended unexpectedly')
    def invoke(*args,**kwargs):raise error
    with pytest.raises(ModelError) as result:module().generate(calls(tmp_path,invoke),'call','ECON','secret prompt',32768)
    assert result.value is error
    saved=json.loads(next(tmp_path.rglob('*.json')).read_bytes())
    assert saved['message_code']=='stream_ended' and saved['model']=='gpt-6.1-sol'
    assert 'secret prompt' not in json.dumps(saved)


def test_unknown_error_text_and_diagnostic_values_are_not_copied(tmp_path):
    def invoke(*args,**kwargs):raise ModelError('sensitive-token-value',diagnostics={'header':'another-secret'})
    with pytest.raises(ModelError):module().generate(calls(tmp_path,invoke),'call','ECON','prompt',32768)
    saved=next(tmp_path.rglob('*.json')).read_text()
    assert 'sensitive-token-value' not in saved and 'another-secret' not in saved
    assert json.loads(saved)['message_code']=='unclassified_codex_error'


def test_success_preserves_exact_reply_without_creating_error_trace(tmp_path):
    reply=object();received=[]
    def invoke(*args,**kwargs):received.append((args,kwargs));return reply
    assert module().generate(calls(tmp_path,invoke),'call','ECON','prompt',32768) is reply
    assert received==[(('call','ECON','prompt'),{'max_output_tokens':32768})]
    assert not list(tmp_path.rglob('*.json'))
