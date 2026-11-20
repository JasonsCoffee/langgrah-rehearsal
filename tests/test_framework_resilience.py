"""Frozen regression evidence from the lobby rehearsal; all providers are fakes."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest
from test_contracts import bundle, load
from test_workspaces import workspace
from test_local_executor import local, run
from test_model_coding_workers import Calls
from unity_coder.core.ai_models import ModelError
from unity_coder.core.coding_workers import ModelCodingWorkers
from unity_coder.core.local_executor import TestReviewRejected, WorkerPatch
from unity_coder.core.verification import VerificationResult


@pytest.mark.parametrize('reply', ['not json', '{"files":{},"reason":""}',
    '{"files":{"../outside":"secret"},"reason":"change"}'])
def test_bad_patch_is_sanitized_operational_error(bundle, reply):
    contract = load(bundle)
    workers = ModelCodingWorkers(contract, Calls('coder','one',reply), Calls('judge','two',''))
    with pytest.raises(ModelError, match='structured output') as error:
        workers.code(contract.units[1], 'green', {}, '', 'paid')
    assert reply not in str(error.value)
    assert error.value.diagnostics['stage'] == 'green'


@pytest.mark.parametrize('reply', ['not json', '{"valid":1,"explanation":"bad"}',
    '{"valid":true,"explanation":""}'])
def test_bad_review_is_operational_not_test_rejection(bundle, reply):
    contract = load(bundle)
    workers = ModelCodingWorkers(contract, Calls('coder','one',''), Calls('judge','two',reply))
    with pytest.raises(ModelError):
        workers.review_tests(contract.units[0], {}, 'paid-review')


def test_real_review_rejection_keeps_actionable_explanation(bundle):
    contract = load(bundle)
    workers = ModelCodingWorkers(contract, Calls('coder','one',''),
        Calls('judge','two','{"valid":false,"explanation":"Missing boundary assertion"}'))
    with pytest.raises(TestReviewRejected, match='Missing boundary assertion'):
        workers.review_tests(contract.units[0], {}, 'review')


def test_invalid_classification_is_operational(bundle):
    contract = load(bundle)
    workers = ModelCodingWorkers(contract, Calls('coder','one',''), Calls('judge','two','not json'))
    evidence = VerificationResult(None, 'tests', 'failed')
    with pytest.raises(ModelError):
        workers.judge(contract.units[1], evidence, {}, 'judge')


@pytest.mark.parametrize('stage', ['test_authoring','green','refactor','test_review','defect_judgment'])
@pytest.mark.parametrize('bad', ['missing','changed'])
def test_required_context_blocks_every_paid_stage(bundle, stage, bad):
    contract = load(bundle)
    coder = Calls('coder','one','{"files":{},"reason":"done"}')
    judge = Calls('judge','two','{"valid":true,"explanation":"covered"}')
    path = 'specs/guide.md'
    unit = contract.units[0 if stage in ('test_authoring','test_review') else 1]
    workers = ModelCodingWorkers(contract, coder, judge,
        context_requirements={unit.id:{path:sha256(b'original').hexdigest()}})
    files = {} if bad == 'missing' else {path:'changed'}
    with pytest.raises(ModelError, match='context'):
        if stage == 'test_review': workers.review_tests(unit,files,'review')
        elif stage == 'defect_judgment': workers.judge(unit,VerificationResult(None,'tests','failed'),files,'judge')
        else: workers.code(unit,stage,files,'','code')
    assert not coder.prompts and not judge.prompts


def test_context_manifest_binds_exact_supplied_text_and_copies_requirements(bundle):
    contract = load(bundle)
    coder = Calls('coder','one','{"files":{},"reason":"unchanged"}')
    requirements = {contract.units[1].id:{'specs/guide.md':sha256('原文\r\n'.encode()).hexdigest()}}
    workers = ModelCodingWorkers(contract,coder,Calls('judge','two',''),context_requirements=requirements)
    requirements.clear()
    files = {'specs/guide.md':'原文\r\n'}
    workers.code(contract.units[1],'green',files,'','code')
    payload = json.loads(coder.prompts[0][2].partition('\n')[2])
    assert payload['context_manifest']['files'] == {'specs/guide.md':sha256('原文\r\n'.encode()).hexdigest()}
    assert payload['context_manifest']['contract_sha256'] == contract.sha256
    assert payload['files'] == files
    assert files == {'specs/guide.md':'原文\r\n'}


@pytest.mark.parametrize('bad', ['unknown-unit','bad-path','bad-hash'])
def test_invalid_context_policy_fails_at_composition(bundle, bad):
    contract = load(bundle)
    policy = {contract.units[0].id:{'specs/guide.md':'a'*64}}
    if bad == 'unknown-unit': policy = {'unknown':policy[contract.units[0].id]}
    elif bad == 'bad-path': policy[contract.units[0].id] = {'../escape':'a'*64}
    else: policy[contract.units[0].id]['specs/guide.md'] = 'not-hash'
    with pytest.raises(ValueError):
        ModelCodingWorkers(contract,Calls('coder','one',''),Calls('judge','two',''),context_requirements=policy)


def test_bad_paid_output_retains_charge_and_never_replays(tmp_path, bundle):
    from test_ai_models import config, response
    from unity_coder.core.ai_models import load_ai_config, ModelClient
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.model_calls import ModelCalls
    contract = load(bundle)
    settings = load_ai_config(config(tmp_path))
    ledger = BudgetLedger(tmp_path/'state','run',input_limit=100000,output_limit=100000,max_cycles=3,max_added_units=2)
    ledger.begin_cycle(1,contract.sha256,{u.id:(u.id,) for u in contract.units})
    seen = []
    def send(*args):
        seen.append(1)
        result = response()
        result['choices'][0]['message']['content'] = 'malformed secret payload'
        return result
    coder = ModelCalls(ModelClient(settings.coder,transport=send),ledger,'run')
    workers = ModelCodingWorkers(contract,coder,Calls('judge','other',''))
    for _ in range(2):
        with pytest.raises(ModelError): workers.code(contract.units[1],'green',{},'','same-call')
    assert len(seen) == 1 and ledger.totals() == (8,2)
    receipt = next((tmp_path/'state/.agent/runs/run/model-calls').glob('*.json'))
    assert json.loads(receipt.read_bytes())['reply']['text'] == 'malformed secret payload'


def test_malformed_output_stops_normally_without_attempt_or_freeze(local):
    executor,services,workers,verified,_,_ = local
    contract = executor.contract
    configured = ModelCodingWorkers(contract,Calls('coder','one','malformed'),Calls('judge','two',''))
    workers.code = configured.code
    executor.advance('prepare'); executor.advance('red')
    result = run(executor)
    assert result['outcome'] == 'operational'
    assert all(services.retry.state(u).failed_attempts == 0 for u in services.tdd.units)
    assert services.tdd.frozen
    assert len(verified) == 1


@pytest.fixture
def two_local(bundle,tmp_path):
    data,_ = bundle
    peer = deepcopy(data['units'][0]); peer['id'] = 'U3-tests'
    peer['owns'] = ['Tests/Runtime/Script/PeerTests.cs']
    peer['acceptance'] = ['Peer.Behavior']
    data['units'].append(peer)
    data['units'][1]['acceptance'].append('Peer.Behavior')
    data['task_links'][0]['unit_ids'].append('U3-tests')
    data['test_links'].append({'test_id':'Peer.Behavior','author_unit':'U3-tests',
        'implementing_units':['U1-state'],'criterion':peer['spec_ref']})
    return local.__wrapped__(workspace.__wrapped__(bundle,tmp_path),tmp_path)


def test_author_feedback_is_per_unit_and_survives_reopen(two_local):
    from test_production_effect_recovery import reopen
    executor,services,workers,_,_,_ = two_local
    reviews = {}; authored = []
    def review(unit,files,operation):
        reviews[unit.id] = reviews.get(unit.id,0)+1
        if reviews[unit.id] == 1: raise TestReviewRejected('repair '+unit.id)
        return 'covered'
    def author(unit,stage,files,feedback,operation):
        authored.append((unit.id,feedback))
        return WorkerPatch({},'source retained for regression fixture')
    workers.review_tests = review; workers.code = author
    executor.advance('prepare')
    reopened = reopen(executor,services)
    executor.advance('prepare'); executor.advance('prepare')
    assert authored == [('U0-tests','repair U0-tests'),('U0-tests',''),('U3-tests','repair U3-tests')]
    assert reopened.state['preparation_feedback'] == {}


def test_effect_resolution_requires_matching_pending_identity_and_evidence(local):
    executor,services,_,_,_,_ = local
    effects = services.effects
    identity = {'stage':'test_authoring','unit':'U0-tests','base':'exact'}
    effects.write('pending',{'identity':identity})
    original = (executor.root/effects.prefix/'pending.json').read_bytes()
    seen = []
    with pytest.raises(ValueError):
        effects.reconcile_call('pending',dict(identity,base='stale'),reconcile=lambda record:seen.append(record))
    assert not seen
    with pytest.raises(ValueError):
        effects.reconcile_call('pending',identity,reconcile=lambda record:None)
    assert (executor.root/effects.prefix/'pending.json').read_bytes() == original
    evidence = executor.root/'proof.json'; evidence.write_bytes(b'actual paid receipt and source proof')
    result = {'files':{},'reason':'exact admitted source retained'}
    resolution = {'result':result,'evidence':{'proof.json':sha256(evidence.read_bytes()).hexdigest()}}
    effects.reconcile_call('pending',identity,reconcile=lambda record:resolution)
    assert effects.call('pending',identity,lambda:pytest.fail('no replay')) == result
    record = effects.read('pending')
    assert record['reconciliation']['pending_sha256'] == sha256(original).hexdigest()
    with pytest.raises(ValueError):
        effects.reconcile_call('pending',identity,reconcile=lambda record:resolution)


@pytest.mark.parametrize('bad',['missing','changed','empty','non-json'])
def test_effect_resolution_never_admits_unproven_output(local,bad):
    executor,services,_,_,_,_ = local
    effects=services.effects; identity={'unit':'U0-tests'}
    effects.write('pending',{'identity':identity})
    proof=executor.root/'proof.json';proof.write_bytes(b'proof')
    resolution={'result':{},'evidence':{'proof.json':sha256(b'proof').hexdigest()}}
    if bad=='missing':proof.unlink()
    elif bad=='changed':proof.write_bytes(b'changed')
    elif bad=='empty':resolution['evidence']={}
    else:resolution['result']={'not-json':object()}
    with pytest.raises((ValueError,OSError,TypeError)):
        effects.reconcile_call('pending',identity,reconcile=lambda record:resolution)
    assert 'result' not in effects.read('pending')
