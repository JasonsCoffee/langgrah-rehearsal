"""Owner-focused model input; actual verification always retains every test."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import PurePosixPath
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from unity_coder.core.contracts import Contract
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.local_executor import LocalExecutionServices


def scoped(unit: str, files: dict[str,str]) -> dict[str,str]:
    suites={'SHELL':(), 'ECON':('LobbyEconomy',), 'MATCH':('LobbyMatch',),
            'SOCIAL':('LobbySocial','LobbyChat'),
            'RECORDS':('LobbyRecords','LobbySocialPartner')}
    if unit not in suites:raise ValueError('Unknown implementation context scope')
    keep=('LobbyHarness','LobbyPresentation','LobbySocialPartnerPriority')+suites[unit]
    omitted={p:sha256(v.encode()).hexdigest() for p,v in files.items()
             if p.startswith('Tests/') and not PurePosixPath(p).name.startswith(keep)}
    result={p:v for p,v in files.items() if p not in omitted}
    result['readonly-context-scope/provenance.json']=json.dumps({
        'unit':unit,'omitted_provided_text_sha256':omitted,
        'complete_specification_criteria_owned_sources_and_failure_evidence_preserved':True,
        'note':'Only unrelated read-only suite bodies are omitted from this model prompt. All physical tests and full verification selection remain unchanged. Hashes describe provided text, not the physical frozen-file inventory.'},ensure_ascii=False)
    return result


def validate_stop(result: dict, transaction: dict, failure: dict, charge: dict) -> None:
    if (result.get('contract_version')!=67
        or result.get('contract_sha256')!='013c774cf990ebacc14e4cb4fcbddf954bb3aadb5ce2abfdd9885d7dc29e3783'
        or result.get('candidate_revision')!='1864d5b240a6ccfe36e8ba06fabdbb6f076c206b'
        or result.get('outcome')!='operational' or transaction.get('complete') is not True
        or transaction.get('stage')!='code' or transaction.get('operation')!='v67-step3-code'
        or failure!={'protocol_phase':'item_validation','item_type':'contextCompaction','event_method':'item/started'}
        or charge!={'reserved':[6251091,65536],'unit':'SHELL','version':67}):
        raise ValueError('Exact rejected compaction and unchanged charge required')


def reconcile(state: Path,contract: Contract,budget: BudgetLedger,
              services: LocalExecutionServices,integration: Path) -> bool:
    from codex_context_recovery import register_retained_call
    from operational_transport import retained_run_reservations
    from unity_coder.core.storage import atomic_write
    from unity_coder.core.workspaces import git
    run=state/'.agent/runs/monopoly-game-lobby';call='v67-step3-code-SHELL'
    key=sha256(call.encode()).hexdigest();raw=(run/'model-calls'/(key+'.json')).read_bytes()
    record=json.loads(raw);result=json.loads((run/'result.json').read_bytes());charge=budget._read()['calls'][call]
    validate_stop(result,services.effects.read('transaction'),record.get('failure'),charge)
    if (contract.sha256!=result['contract_sha256'] or budget.limits!=[250000000,24000000,160,2]
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or not services.tdd.frozen):
        raise ValueError('Candidate, aggregate grant or global freeze changed')
    services.tdd.assert_frozen();frozen=services.tdd._frozen_hashes
    if len(frozen)!=189 or sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()!='03aeaba0e7597069ab59c1a98f9b0a664f3f7e7ff64e73c36d5939779fce32c5':
        raise ValueError('Complete frozen inventory changed')
    plan=services.effects.read('code-v67-step3-code');worker=services.effects.read('worker-v67-step3-code-SHELL')
    if (not plan or plan['group']!=['SHELL'] or plan['stage']!='green'
        or plan['base']!=result['candidate_revision'] or not worker or 'result' in worker):
        raise ValueError('Unexpected pending implementation effects')
    digest='41eaf6c280d0145afdff0061dd2576dd5f38c3f36670eca2eded3c2f6229ee34'
    register_retained_call(state,call,charge,digest)
    retained=retained_run_reservations(state,budget._read())
    if len(retained)!=25:raise ValueError('All 25 uncertain reservations must remain')
    atomic_write(state,'recovery-authorizations/v67-compaction-scope.json',json.dumps({
        'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],
        'failed_receipt_sha256':digest,'retained_uncertain':retained,'usage':budget.totals(),
        'reason':'Owner-scoped complete test suites and shared harness/presentation retained; unrelated suite bodies become hashed provenance. All criteria, specification, owned code, actual failure evidence and full verification remain.',
        'prior_call_replayed':False,'human_accepted':False},indent=2).encode())
    return True
