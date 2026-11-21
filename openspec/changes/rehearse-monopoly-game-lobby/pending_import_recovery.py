"""Resolve one exact import interruption using real candidate-bound verification."""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import TYPE_CHECKING
from unity_coder.core.storage import atomic_write
from unity_coder.core.verification import VerificationRequest
from unity_coder.core.workspaces import git
if TYPE_CHECKING:
    from unity_coder.core.budget import BudgetLedger
    from unity_coder.core.contracts import Contract
    from unity_coder.core.executor import ProductionExecutor
    from unity_coder.core.local_executor import LocalExecutionServices
    from unity_coder.core.verification import VerificationLadder
    from overlay_host import OverlayHost

OPERATION='v68-step7-verify'
CANDIDATE='d6304a1b906bb340eeedccb01c57dc1393d02fe3'
CONTRACT='a3c9baa004dabeb77eec0b233ee03d18deb3dc45a31e90134356c4a4748b736e'


def validate_pending(executor: dict,transaction: dict,effect: dict,submitted: bool) -> None:
    request=effect.get('identity',{}).get('request',{})
    if (executor.get('stage')!='verify' or executor.get('pending')!=OPERATION
        or executor.get('contract_version')!=68 or executor.get('contract_sha256')!=CONTRACT
        or transaction.get('stage')!='verify' or transaction.get('operation')!=OPERATION
        or transaction.get('complete') is not False or 'result' in effect or submitted
        or request.get('request_id')!=OPERATION or request.get('candidate_revision')!=CANDIDATE
        or request.get('contract_version')!=68 or request.get('contract_sha256')!=CONTRACT):
        raise ValueError('Only the exact unsubmitted interrupted import can be reconciled')


def reconcile(state: Path,contract: Contract,budget: BudgetLedger,services: LocalExecutionServices,
              executor: ProductionExecutor,host: OverlayHost,ladder: VerificationLadder,
              frozen_paths: tuple[str,...]) -> None:
    from operational_transport import retained_run_reservations
    from compile_repair_context import attribute_compile
    source=services.integration.path;effect=services.effects.read('verify-'+OPERATION)
    if effect is None:raise ValueError('No matching pending verification effect')
    wire=effect['identity']['request'];folders={}
    for mode in ('compile','tests'):
        key=sha256(json.dumps({'request':wire,'mode':mode},sort_keys=True).encode()).hexdigest()
        folders[mode]=host.host/'.agent/verification'/key
    submitted=any((folder/name).exists() for folder in folders.values() for name in ('request.json','result.json'))
    validate_pending(executor._read(),services.effects.read('transaction') or {},effect,submitted)
    if (contract.sha256!=CONTRACT or git(source,'rev-parse','HEAD').decode().strip()!=CANDIDATE
        or git(source,'status','--porcelain') or not services.tdd.frozen):
        raise ValueError('Candidate or global freeze changed')
    services.tdd.assert_frozen();tests=services.tdd._frozen_hashes
    if len(tests)!=195 or sha256(json.dumps(tests,sort_keys=True).encode()).hexdigest()!='28fec4be892147775c869eb39ebf8e9a899ed869e3602f0606f950c44db06800':
        raise ValueError('Complete frozen inventory changed')
    before=budget._read()
    if len(retained_run_reservations(state,before))!=25:raise ValueError('Uncertain reservations changed')
    host.preflight()
    if host.overlay.read()['candidate']!=CANDIDATE:raise ValueError('Host is not the already materialized candidate')
    prefix='recovery-authorizations/import-v68'
    atomic_write(state,prefix+'-intent.json',json.dumps({'operation':OPERATION,'candidate':CANDIDATE,
        'contract_sha256':CONTRACT,'zero_explicit_verification_submissions':True,
        'reason':'Observed import-settlement timeout; exact Bridge now reports ready. Complete full import/baseline checks before submitting the original verification once.',
        'usage':budget.totals(),'frozen_count':195,'human_accepted':False},indent=2).encode())
    request=VerificationRequest(**(wire|{'test_selection':tuple(wire['test_selection'])}))
    try:
        metadata=host.overlay.capture_import(CANDIDATE)
    except ValueError as error:
        if str(error)!='Baseline or candidate bytes drifted: Assets/JJGame/monopoly/Runtime/Script/Monopoly.cs':raise
        from generated_entry_reconciliation import report
        actual=report(host,source,request,tests)
        print('RECONCILED ACTUAL IMPORT DRIFT',OPERATION,flush=True)
    else:
        if metadata:raise ValueError('Unexpected imported metadata must be reconciled separately')
        services.tdd.assert_frozen()
        paths=git(source,'ls-tree','-r','--name-only','-z','HEAD').decode().split('\0')
        contents={p:(source/p).read_bytes() for p in paths if p}
        patches={u:{p:bytes.fromhex(v) if v is not None else None for p,v in files.items()}
                 for u,files in services.state['patches'].items()}
        print('RECONCILING ORIGINAL VERIFICATION',OPERATION,CANDIDATE,flush=True)
        actual=host.verify(request,ladder,contract,source,patches,contents,frozen_paths)
    actual=attribute_compile(contract,actual,lambda key,proof:atomic_write(state,
        'diagnostics/compile-attribution-'+key+'.json',json.dumps(proof,indent=2).encode()))
    if actual.request!=request:raise ValueError('Stale actual verification response')
    services.tdd.assert_frozen()
    if budget._read()!=before:raise ValueError('Recovery unexpectedly changed model accounting')
    if services.effects.read('verify-'+OPERATION)!=effect:raise ValueError('Pending effect changed during reconciliation')
    # Trusted effect-owner reconciliation: store only the real ladder result.
    services.effects.write('verify-'+OPERATION,effect|{'result':asdict(actual)})
    atomic_write(state,prefix+'-complete.json',json.dumps({'operation':OPERATION,'candidate':CANDIDATE,
        'actual_result':asdict(actual),'usage_unchanged':budget.totals(),'frozen_count':195,
        'new_candidate_created':False,'human_accepted':False},indent=2).encode())
    print('RECONCILED',actual.gate,actual.status,len(actual.violations),flush=True)
