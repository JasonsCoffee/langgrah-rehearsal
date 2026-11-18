"""Local secret configuration and provider boundary stay offline in tests."""
import json
import pytest
from unity_coder.core.ai_models import load_ai_config, ModelClient, ModelError


def config(tmp_path, coder='coder-model', judge='judge-model', endpoint='https://openrouter.ai/api/v1'):
    p=tmp_path/'ai.local.toml'
    p.write_text(f'''[coder]
provider="OpenRouter"
model="{coder}"
api_key="private-test-key"
base_url="{endpoint}"
[judge]
provider="OpenRouter"
model="{judge}"
api_key="private-test-key"
base_url="{endpoint}"
''')
    return p


def response():
    return {'id':'call1','model':'judge-model','choices':[{'finish_reason':'stop','message':{'content':'OK'}}],
            'usage':{'prompt_tokens':8,'completion_tokens':2}}


def test_loads_distinct_models_without_secret_repr(tmp_path):
    c=load_ai_config(config(tmp_path))
    assert c.coder.provider=='openrouter' and c.judge.model=='judge-model'
    assert 'private-test-key' not in repr(c)


@pytest.mark.parametrize('coder,judge,endpoint', [('same','same','https://openrouter.ai/api/v1'),
    ('','judge','https://openrouter.ai/api/v1'),('coder','judge','http://openrouter.ai/api/v1'),
    ('coder','judge','https://user:pass@openrouter.ai/api/v1'),
    ('coder','judge','https://openrouter.ai/api/v1?key=secret')])
def test_invalid_config_fails_closed(tmp_path,coder,judge,endpoint):
    with pytest.raises(ValueError): load_ai_config(config(tmp_path,coder,judge,endpoint))


def test_judge_forces_zero_and_requires_supported_parameters(tmp_path):
    c=load_ai_config(config(tmp_path)); seen=[]
    def send(url,key,payload,timeout):
        seen.append((url,payload)); return response()
    result=ModelClient(c.judge,transport=send).generate('Evaluate evidence',max_output_tokens=32)
    assert seen[0][0]=='https://openrouter.ai/api/v1/chat/completions'
    assert seen[0][1]['temperature']==0
    assert seen[0][1]['provider']['require_parameters'] is True
    assert result.text=='OK' and result.input_tokens==8 and result.output_tokens==2


@pytest.mark.parametrize('change', ['error','empty','truncated','usage'])
def test_invalid_provider_responses_are_not_success(tmp_path,change):
    c=load_ai_config(config(tmp_path)); r=response()
    if change=='error': r={'error':{'message':'private-test-key echoed by gateway'}}
    elif change=='empty': r['choices'][0]['message']['content']=''
    elif change=='truncated': r['choices'][0]['finish_reason']='length'
    else: r['usage']['prompt_tokens']=-1
    with pytest.raises(ModelError) as caught:
        ModelClient(c.coder,transport=lambda *args:r).generate('ping',max_output_tokens=32)
    assert 'private-test-key' not in str(caught.value)


def test_transport_error_is_redacted_and_not_retried(tmp_path):
    c=load_ai_config(config(tmp_path)); calls=[]
    def send(*args):
        calls.append(1); raise OSError('private-test-key')
    with pytest.raises(ModelError) as caught:
        ModelClient(c.coder,transport=send).generate('ping',max_output_tokens=32)
    assert len(calls)==1 and 'private-test-key' not in str(caught.value)
