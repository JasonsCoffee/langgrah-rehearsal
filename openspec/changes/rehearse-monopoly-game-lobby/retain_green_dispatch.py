"""Append provenance for the five uncertain Green calls; never amend a charge."""
from hashlib import sha256
import json
import os
from pathlib import Path
from unity_coder.core.storage import atomic_write
from codex_lobby import retained_codex_call
from operational_transport import retained_run_reservations


def main() -> None:
    state=Path(os.environ['LOBBY_RUN_ROOT'])/'trusted-state'
    run=state/'.agent/runs/monopoly-game-lobby'
    ledger=json.loads((run/'budget.json').read_bytes())
    path='model-authorizations/codex-retained-calls.json'
    raw=(state/path).read_bytes();manifest=json.loads(raw)
    if ledger['limits']!=[100000000,12000000,80,2]:raise ValueError('Unexpected budget; no reset')
    for unit in ('SHELL','ECON','SOCIAL','RECORDS','MATCH'):
        call='v63-step4-code-'+unit;charge=ledger['calls'][call]
        record=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes()
        proof={'charge':charge,'receipt_sha256':sha256(record).hexdigest()}
        retained_codex_call(state,call,charge,proof)
        if call in manifest['calls'] and manifest['calls'][call]!=proof:raise ValueError('Prior proof changed')
        manifest['calls'][call]=proof
    if json.loads(raw)!=manifest:
        history='model-authorizations/codex-retention-history/'+sha256(raw).hexdigest()+'.json'
        if (state/history).exists() and (state/history).read_bytes()!=raw:raise ValueError('History changed')
        atomic_write(state,history,raw)
        atomic_write(state,path,json.dumps(manifest,indent=2).encode())
    retained=retained_run_reservations(state,ledger)
    if len(retained)!=23:raise ValueError('Expected all twenty-three reservations')
    approval={'authority':'explicit_user_session','source':'request_user_input_async call_9a7d5274098c49399893f736f5dff0c0',
        'reply':'Approve 125M input; keep 12M output / 80 cycles',
        'approved_limits':{'input_limit':125000000,'output_limit':12000000,'max_cycles':80},
        'preserve_all_charges_and_reservations':True,'human_acceptance_granted':False}
    approval_path='budget-amendments/input-125m-user-approval.json'
    if (state/approval_path).exists() and json.loads((state/approval_path).read_bytes())!=approval:
        raise ValueError('Approval identity changed')
    atomic_write(state,approval_path,json.dumps(approval,indent=2).encode())
    print(json.dumps({'retained_uncertain':len(retained),'limits_applied':ledger['limits'],'approved_input_pending_native_recovery':125000000}))


if __name__=='__main__':main()
