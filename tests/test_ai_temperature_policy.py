import pytest
from test_ai_models import config, response
from unity_coder.core.ai_models import load_ai_config, ModelClient


def test_explicit_provider_temperature_omits_parameter_and_preserves_effort(tmp_path):
    path=config(tmp_path)
    path.write_text(path.read_text().replace('[judge]', '[judge]\ntemperature_mode="provider"\neffort="medium"'))
    settings=load_ai_config(path)
    seen=[]
    def send(url,key,payload,timeout): seen.append(payload); return response()
    ModelClient(settings.judge,transport=send).generate('Review',max_output_tokens=512)
    assert 'temperature' not in seen[0]
    assert seen[0]['reasoning']=={'effort':'medium'}
    assert seen[0]['provider']['require_parameters'] is True
    assert settings.coder.temperature_mode=='zero'


def test_unknown_temperature_policy_fails_closed(tmp_path):
    path=config(tmp_path)
    path.write_text(path.read_text().replace('[judge]', '[judge]\ntemperature_mode="automatic-fallback"'))
    with pytest.raises(ValueError): load_ai_config(path)
