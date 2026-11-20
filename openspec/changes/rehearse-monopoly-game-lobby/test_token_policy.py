"""Offline composition checks; importing the host never invokes a run."""
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import pytest

from unity_coder.core.coding_workers import StageTokenBudgets
from unity_coder.core.verification import VerificationResult


def test_rehearsal_uses_one_policy_for_every_paid_stage(monkeypatch, tmp_path):
    directory = Path(__file__).parent
    monkeypatch.syspath_prepend(str(directory))
    host = runpy.run_path(str(directory/'lobby_production_host.py'))
    path = tmp_path/'policy.json'
    path.write_text(json.dumps({'stage_output_tokens': {
        'test_authoring': 71001, 'green': 71002, 'refactor': 71003,
        'test_review': 71004, 'defect_judgment': 71005}, 'max_context_bytes': 600000}))
    policy, context_limit = host['load_token_policy'](path)
    seen = []
    class Calls:
        def __init__(self, role):
            self.client = SimpleNamespace(config=SimpleNamespace(role=role, model=role))
        def generate(self, call_id, unit, prompt, *, max_output_tokens):
            seen.append((call_id, max_output_tokens))
            text = ('{"valid":true,"explanation":"covered"}' if call_id == 'review'
                    else '{"defect_class":"implementation","explanation":"repair"}' if call_id == 'judge'
                    else '{"files":{},"reason":"prepared"}')
            return SimpleNamespace(text=text)
    contract = SimpleNamespace(spec=SimpleNamespace(path='spec.md'), test_links=(), units=())
    worker = host['ContextWorkers'](contract, Calls('coder'), Calls('judge'), tmp_path,
                                    token_budgets=policy, max_context_bytes=context_limit)
    worker.context = lambda unit, files: files
    unit = SimpleNamespace(id='TEST-X', role='test', owns=(), acceptance=(), instructions='task')
    worker.code(unit, 'test_authoring', {}, '', 'author')
    unit.role = 'impl'
    worker.code(unit, 'green', {}, '', 'green')
    worker.code(unit, 'refactor', {}, '', 'refactor')
    worker.review_tests(unit, {}, 'review')
    worker.judge(unit, VerificationResult(None, 'tests', 'failed'), {}, 'judge')
    assert seen == [('author',71001), ('green',71002), ('refactor',71003),
                    ('review',71004), ('judge',71005)]
    assert context_limit == 600000


def test_checked_in_policy_explicitly_allocates_every_stage():
    policy = json.loads(Path(__file__).with_name('token-policy.json').read_bytes())
    assert StageTokenBudgets(**policy['stage_output_tokens']) == StageTokenBudgets()
    assert policy['max_context_bytes'] > 0


@pytest.mark.parametrize('change', ['missing_stage', 'extra_field', 'boolean_context', 'zero_context', 'bad_stage'])
def test_policy_rejects_partial_or_invalid_configuration(monkeypatch, tmp_path, change):
    directory = Path(__file__).parent
    monkeypatch.syspath_prepend(str(directory))
    host = runpy.run_path(str(directory/'lobby_production_host.py'))
    data = {'stage_output_tokens': dict(test_authoring=65536, green=65536, refactor=65536,
                                       test_review=32768, defect_judgment=32768),
            'max_context_bytes': 600000}
    if change == 'missing_stage': del data['stage_output_tokens']['refactor']
    elif change == 'extra_field': data['unexpected'] = 1
    elif change == 'boolean_context': data['max_context_bytes'] = True
    elif change == 'zero_context': data['max_context_bytes'] = 0
    else: data['stage_output_tokens']['test_review'] = -1
    path = tmp_path/'policy.json'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        host['load_token_policy'](path)
