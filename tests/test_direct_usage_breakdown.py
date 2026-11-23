"""Cache/reasoning breakdowns never replace or double-count billed totals."""
from pathlib import Path
from hashlib import sha256
import json
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def response(finish='stop'):
    return {'id':'reply','model':'deepseek-flash','usage':{'prompt_tokens':50,'completion_tokens':60,
        'prompt_cache_hit_tokens':20,'prompt_cache_miss_tokens':30,
        'completion_tokens_details':{'reasoning_tokens':40},'prompt_tokens_details':{'cached_tokens':20}},
        'choices':[{'finish_reason':finish,'message':{'content':'{"ok":true}'}}]}


def test_success_keeps_full_totals_and_nested_breakdowns():
    from direct_deepseek_client import DirectDeepSeekClient
    client=DirectDeepSeekClient('fake',transport=lambda *args:response())
    reply=client.generate('prompt',max_output_tokens=100)
    assert (reply.input_tokens,reply.output_tokens)==(50,60)
    assert client.last_usage['reasoning_tokens']==40
    assert client.last_usage['cached_tokens']==20


def test_rejected_completion_still_records_reported_breakdown(tmp_path):
    from direct_deepseek_client import DirectDeepSeekClient
    from unity_coder.core.ai_models import ModelError
    client=DirectDeepSeekClient('fake',transport=lambda *args:response('length'),state=tmp_path)
    with pytest.raises(ModelError):client.generate_operation('op','prompt',max_output_tokens=100)
    path=tmp_path/'direct-usage'/(sha256(b'op').hexdigest()+'.json')
    record=json.loads(path.read_bytes())
    assert record['complete'] is False and record['usage']['completion_tokens']==60
    assert record['usage']['reasoning_tokens']==40


def test_unknown_failure_cannot_inherit_previous_usage(tmp_path):
    from direct_deepseek_client import DirectDeepSeekClient
    from unity_coder.core.ai_models import ModelError
    client=DirectDeepSeekClient('fake',transport=lambda *args:response(),state=tmp_path)
    client.generate_operation('first','prompt',max_output_tokens=100)
    def broken(*args):raise ModelError('unknown submission')
    client.transport=broken
    with pytest.raises(ModelError):client.generate_operation('unknown','prompt',max_output_tokens=100)
    assert client.last_usage=={}
