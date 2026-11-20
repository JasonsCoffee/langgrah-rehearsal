"""Target-only context policy and proof-bound recovery before a paid call."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git
if TYPE_CHECKING:
    from unity_coder.core.effects import DurableEffects
    from unity_coder.core.local_executor import LocalExecutionServices
    from unity_coder.core.contracts import Contract
    from unity_coder.core.budget import BudgetLedger
    from lobby_production_host import ContextWorkers


def enforce_context_limit(size: int, limit: int, coder_provider: str, judge_provider: str) -> None:
    # The Codex route validates the exact final prompt through context_parts,
    # then reserves its staged input in the persistent aggregate ledger. The
    # older byte estimate must not impose another per-request API cap.
    if coder_provider==judge_provider=='codex':return
    if size>limit:raise ValueError('Curated context exceeds the bounded per-call input plan')


def recover_judge_effect(effects: DurableEffects, name: str, identity: dict,
                         paid_evidence: bool, invoke: Callable[[],tuple[str,str]]) -> None:
    identity=json.loads(json.dumps(identity))
    pending=effects.read(name)
    if (not pending or pending.get('identity')!=identity or 'result' in pending or paid_evidence):
        raise ValueError('Only an exact proven unsubmitted Judge intent can be completed')
    classification,reason=invoke()
    if classification not in ('implementation','contract') or not reason:
        raise ValueError('A real valid independent Judge decision is required')
    effects.write(name,{'identity':identity,'result':{'classification':classification,'reason':reason}})


def register_retained_call(state: Path, call: str, charge: dict, expected_sha256: str) -> None:
    key=sha256(call.encode()).hexdigest()
    raw=(state/'.agent/runs/monopoly-game-lobby/model-calls'/(key+'.json')).read_bytes()
    record=json.loads(raw);identity=record['identity']
    claim=json.loads((state/'codex-claims'/identity['backend_policy_sha256']/(key+'.json')).read_bytes())
    if (sha256(raw).hexdigest()!=expected_sha256 or 'actual' in charge or 'reply' in record
        or 'failure' not in record or identity.get('worker_backend')!='codex_app_server'
        or identity.get('provider')!='codex' or identity.get('call_id')!=call
        or charge.get('unit')!=identity.get('unit_id') or not call.startswith('v'+str(charge.get('version'))+'-')
        or claim!={'operation_id':call,'policy_sha256':identity['backend_policy_sha256'],'prompt_sha256':identity['prompt_sha256']}
        or len(charge.get('reserved',[]))!=2 or any(type(n) is not int or n<=0 for n in charge['reserved'])
        or (state/'codex-receipts'/(key+'.json')).exists()):
        raise ValueError('Exact uncertain failed-call receipt, claim and reservation required')
    path='model-authorizations/codex-retained-calls.json';prior=json.loads((state/path).read_bytes())
    proof={'receipt_sha256':expected_sha256,'charge':charge}
    if call in prior['calls'] and prior['calls'][call]!=proof:raise ValueError('Historical retention proof changed')
    prior['calls'][call]=proof
    atomic_write(state,path,json.dumps(prior,indent=2).encode())


def reconcile(state: Path, contract: Contract, budget: BudgetLedger,
              services: LocalExecutionServices, workers: ContextWorkers, integration: Path) -> None:
    from full_baseline_restoration import assert_tests
    from operational_transport import retained_run_reservations
    from unity_coder.core.local_executor import _verification
    run=state/'.agent/runs/monopoly-game-lobby';operation='v66-step8-verify'
    call=operation+'-judge-SHELL';key=sha256(call.encode()).hexdigest()
    current=json.loads((run/'executor-v66.json').read_bytes())
    tx=services.effects.read('transaction');candidate='48bcbb766137998ce0264b726169b014adabc56e'
    if (contract.contract_version!=66 or contract.sha256!='65061cc3537f2d22830aaf77f698799427efd846c4724824be5039040699251b'
        or current['stage']!='verify' or current['pending']!=operation
        or not tx or tx['operation']!=operation or tx['stage']!='verify' or tx.get('complete')
        or git(integration,'rev-parse','HEAD').decode().strip()!=candidate or git(integration,'status','--porcelain')):
        raise ValueError('Exact interrupted same-run verification required')
    raw=(run/'services-v66/evidence'/f'{operation}.json').read_bytes()
    if sha256(raw).hexdigest()!='3856723fdf3fd5cadaf5b6e9abb33fbe7c902ab99a98b5c3338f347331e21dd1':
        raise ValueError('Completed compile evidence changed')
    value=json.loads(raw);evidence=_verification(value)
    verified=services.effects.read('verify-'+operation)
    if (not verified or verified.get('result')!=value or evidence.gate!='compile' or evidence.status!='failed'
        or evidence.related_units!=('SHELL',) or evidence.request.candidate_revision!=candidate
        or evidence.request.contract_sha256!=contract.sha256 or evidence.request.request_id!=operation):
        raise ValueError('Actual post-audited compiler evidence is required')
    assert_tests(state,66,integration)
    ledger=budget._read();retained_failed=None
    if call in ledger['calls']:
        old_call=call;old_key=key
        historical=ledger|{'calls':{k:v for k,v in ledger['calls'].items() if k!=old_call}}
        if len(retained_run_reservations(state,historical))!=23:raise ValueError('Historical uncertain usage changed')
        old_charge=ledger['calls'][old_call]
        if old_charge!={'reserved':[5848476,32768],'unit':'SHELL','version':66}:
            raise ValueError('Rejected Judge reservation changed')
        register_retained_call(state,old_call,old_charge,'b7b303778bb39f5fd878cd6a3a0360af0a2beac6a5e3a85c47659e39952445e8')
        if len(retained_run_reservations(state,ledger))!=24:raise ValueError('All uncertain calls must remain charged')
        retained_failed={'call':old_call,'charge':old_charge,'receipt_sha256':'b7b303778bb39f5fd878cd6a3a0360af0a2beac6a5e3a85c47659e39952445e8'}
        call=old_call+'-context-recovery-1';key=sha256(call.encode()).hexdigest()
    elif len(retained_run_reservations(state,ledger))!=23:raise ValueError('Historical uncertain usage changed')
    paid=(call in ledger['calls'] or (run/'model-calls'/(key+'.json')).exists()
          or (state/'codex-receipts'/(key+'.json')).exists()
          or any((state/'codex-claims').glob('*/'+key+'.json')))
    identity={'request':asdict(evidence.request),'unit':'SHELL'}
    proof={'operation':call,'candidate':candidate,'contract_sha256':contract.sha256,
           'evidence_sha256':sha256(raw).hexdigest(),'zero_submission':not paid,
           'before_usage':budget.totals(),'retained_failed_call':retained_failed,'human_accepted':False}
    if paid:raise ValueError('A paid intent exists; zero-submission recovery is forbidden')
    atomic_write(state,'context-recovery/v66-intent.json',json.dumps(proof,indent=2).encode())
    unit=services.tdd.units['SHELL']
    recover_judge_effect(services.effects,'judge-'+operation+'-SHELL',identity,paid,
                         lambda:workers.judge(unit,evidence,services._context(),call))
    atomic_write(state,'context-recovery/v66-complete.json',json.dumps(proof|{
        'after_usage':budget.totals(),'actual_judge_effect':'judge-'+operation+'-SHELL'},indent=2).encode())
