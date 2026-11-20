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
    ledger=budget._read()
    if len(retained_run_reservations(state,ledger))!=23:raise ValueError('Historical uncertain usage changed')
    paid=(call in ledger['calls'] or (run/'model-calls'/(key+'.json')).exists()
          or (state/'codex-receipts'/(key+'.json')).exists()
          or any((state/'codex-claims').glob('*/'+key+'.json')))
    identity={'request':asdict(evidence.request),'unit':'SHELL'}
    proof={'operation':call,'candidate':candidate,'contract_sha256':contract.sha256,
           'evidence_sha256':sha256(raw).hexdigest(),'zero_submission':not paid,
           'before_usage':budget.totals(),'human_accepted':False}
    if paid:raise ValueError('A paid intent exists; zero-submission recovery is forbidden')
    atomic_write(state,'context-recovery/v66-intent.json',json.dumps(proof,indent=2).encode())
    unit=services.tdd.units['SHELL']
    recover_judge_effect(services.effects,'judge-'+operation+'-SHELL',identity,paid,
                         lambda:workers.judge(unit,evidence,services._context(),call))
    atomic_write(state,'context-recovery/v66-complete.json',json.dumps(proof|{
        'after_usage':budget.totals(),'actual_judge_effect':'judge-'+operation+'-SHELL'},indent=2).encode())
