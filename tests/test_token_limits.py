"""Frozen regressions for stage allocations, model caps and durable run ceilings."""
from dataclasses import replace
import pytest
from test_ai_models import config, response
from test_contracts import bundle, load
from test_model_coding_workers import Calls
from unity_coder.core.ai_models import load_ai_config, ModelClient, ModelError
from unity_coder.core.budget import BudgetLedger
from unity_coder.core.coding_workers import ModelCodingWorkers
from unity_coder.core.model_calls import ModelCalls
from unity_coder.core.verification import VerificationResult


def paid(tmp_path, send, *, cap=None, output_limit=200000):
    settings = replace(load_ai_config(config(tmp_path)).coder, max_output_tokens=cap)
    ledger = BudgetLedger(tmp_path/'state', 'run', input_limit=20000,
                          output_limit=output_limit, max_cycles=3, max_added_units=2)
    ledger.begin_cycle(1, 'contract', {'A': ('A',)})
    return ModelCalls(ModelClient(settings, transport=send), ledger, 'run'), ledger


def test_large_allowance_reaches_provider_and_replays_without_new_charge(tmp_path):
    seen = []
    calls, ledger = paid(tmp_path, lambda *args: seen.append(args[2]) or response(), cap=131072)
    reply = calls.generate('large', 'A', 'Code', max_output_tokens=65536)
    assert seen[0]['max_completion_tokens'] == 65536
    assert calls.generate('large', 'A', 'Code', max_output_tokens=65536) == reply
    assert len(seen) == 1 and ledger.totals() == (8, 2)
    with pytest.raises(ModelError, match='identity changed'):
        calls.generate('large', 'A', 'Code', max_output_tokens=65537)


def test_omitted_model_cap_has_no_legacy_32768_ceiling(tmp_path):
    calls, _ = paid(tmp_path, lambda *args: response())
    assert calls.generate('large', 'A', 'Code', max_output_tokens=100000).text == 'OK'


def test_model_cap_rejects_before_reservation_or_transport(tmp_path):
    seen = []
    calls, ledger = paid(tmp_path, lambda *args: seen.append(1) or response(), cap=65536)
    with pytest.raises(ModelError, match='model output'):
        calls.generate('large', 'A', 'Code', max_output_tokens=65537)
    assert not seen and ledger.totals() == (0, 0)


@pytest.mark.parametrize('limit', [True, False, 0, -1, 1.5, '65536'])
def test_invalid_output_allocation_never_reserves(tmp_path, limit):
    calls, ledger = paid(tmp_path, lambda *args: pytest.fail('transport reached'))
    with pytest.raises(ValueError):
        calls.generate('bad', 'A', 'Code', max_output_tokens=limit)
    assert ledger.totals() == (0, 0)


def test_run_output_ceiling_still_blocks_large_model_allowance(tmp_path):
    calls, ledger = paid(tmp_path, lambda *args: pytest.fail('transport reached'),
                         cap=131072, output_limit=65535)
    with pytest.raises(ValueError):
        calls.generate('large', 'A', 'Code', max_output_tokens=65536)
    assert ledger.totals() == (0, 0)


def test_run_input_ceiling_still_blocks_dispatch(tmp_path):
    calls, ledger = paid(tmp_path, lambda *args: pytest.fail('transport reached'))
    with pytest.raises(ValueError):
        calls.generate('large', 'A', 'x'*20000, max_output_tokens=65536)
    assert ledger.totals() == (0, 0)


def test_uncertain_large_call_remains_reserved_across_reconstruction(tmp_path):
    seen = []
    def fail(*args):
        seen.append(1)
        raise OSError('timeout')
    calls, ledger = paid(tmp_path, fail)
    with pytest.raises(ModelError):
        calls.generate('large', 'A', 'Code', max_output_tokens=65536)
    assert ledger.totals() == (1028, 65536)
    resumed = ModelCalls(calls.client, BudgetLedger(tmp_path/'state', 'run',
        input_limit=20000, output_limit=200000, max_cycles=3, max_added_units=2), 'run')
    with pytest.raises(ModelError, match='reconciliation'):
        resumed.generate('large', 'A', 'Code', max_output_tokens=65536)
    assert len(seen) == 1 and resumed.budget.totals() == (1028, 65536)


def test_configured_model_cap_loads_without_secret_repr(tmp_path):
    path = config(tmp_path)
    path.write_text(path.read_text().replace('[judge]', 'max_output_tokens=131072\n[judge]'))
    settings = load_ai_config(path)
    assert settings.coder.max_output_tokens == 131072
    assert settings.judge.max_output_tokens is None
    assert 'private-test-key' not in repr(settings)


@pytest.mark.parametrize('value', ['true', '0', '-1', '1.5', '"large"'])
def test_invalid_model_caps_fail_closed(tmp_path, value):
    path = config(tmp_path)
    path.write_text(path.read_text().replace('[judge]', f'max_output_tokens={value}\n[judge]'))
    with pytest.raises(ModelError):
        load_ai_config(path)


def test_every_paid_stage_uses_its_own_configured_allocation(bundle):
    from unity_coder.core.coding_workers import StageTokenBudgets
    contract = load(bundle)
    coder = Calls('coder', 'one', '{"files":{},"reason":"prepared"}')
    judge = Calls('judge', 'two', '{"valid":true,"explanation":"covered"}')
    policy = StageTokenBudgets(test_authoring=70001, green=70002, refactor=70003,
                               test_review=70004, defect_judgment=70005)
    workers = ModelCodingWorkers(contract, coder, judge, token_budgets=policy)
    workers.code(contract.units[0], 'test_authoring', {}, '', 'author')
    workers.code(contract.units[1], 'green', {}, '', 'green')
    workers.code(contract.units[1], 'refactor', {}, '', 'refactor')
    workers.review_tests(contract.units[0], {}, 'review')
    judge.reply = '{"defect_class":"implementation","explanation":"repair"}'
    workers.judge(contract.units[1], VerificationResult(None, 'tests', 'failed'), {}, 'judge')
    assert [p[3] for p in coder.prompts] == [70001, 70002, 70003]
    assert [p[3] for p in judge.prompts] == [70004, 70005]


@pytest.mark.parametrize('value', [True, 0, -1, 1.5])
def test_stage_policy_rejects_invalid_allocations(value):
    from unity_coder.core.coding_workers import StageTokenBudgets
    with pytest.raises(ValueError):
        StageTokenBudgets(refactor=value)


def test_uniform_legacy_override_and_conflicting_policies(bundle):
    from unity_coder.core.coding_workers import StageTokenBudgets
    contract = load(bundle)
    coder = Calls('coder', 'one', '{"files":{},"reason":"prepared"}')
    judge = Calls('judge', 'two', '{"valid":true,"explanation":"covered"}')
    workers = ModelCodingWorkers(contract, coder, judge, max_output_tokens=90000)
    workers.code(contract.units[1], 'refactor', {}, '', 'refactor')
    workers.review_tests(contract.units[0], {}, 'review')
    assert coder.prompts[0][3] == judge.prompts[0][3] == 90000
    with pytest.raises(ValueError):
        ModelCodingWorkers(contract, coder, judge, max_output_tokens=90000,
                           token_budgets=StageTokenBudgets())
