"""Reconcile one settled, wholly unapplied Records generation-length failure."""
from hashlib import sha256
import json
from operational_transport import retained_run_reservations
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git

def reconcile(state,contract,budget,services,integration,settings,workers):
    run=state/'.agent/runs/monopoly-game-lobby'
    result=json.loads((run/'result.json').read_bytes())
    transaction=services.effects.read('transaction')
    call='v54-step4-prepare-TEST-RECORDS-TEST-RECORDS'
    if (contract.contract_version!=54
        or contract.sha256!='09403f79511972b98999231f96135f227a429d8721d499461875673fa5132a93'
        or result['outcome']!='operational'
        or result['candidate_revision']!='8836111270bf4009c65e3d8291510b247cb741fb'
        or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
        or git(integration,'status','--porcelain') or services.tdd.frozen
        or not transaction['complete'] or transaction['operation']!='v54-step4-prepare'
        or settings.coder.model!='deepseek/deepseek-v4.1-flash'
        or settings.judge.model!='openai/gpt-6.1-sol'):
        raise ValueError('Exact Records length recovery identity changed')
    ledger=budget._read();retained=retained_run_reservations(state,ledger)
    raw=(run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')).read_bytes()
    receipt=json.loads(raw)
    if (sha256(raw).hexdigest()!='e9d298a537c4b4f03e0bec64da424b5ce75a23ae4622172d2b1e982b5936a3de'
        or {k:v for k,v in receipt['failure'].items() if k!='partial_content'}!={
            'input_tokens':74291,'output_tokens':65536,'finish_reason':'length'}
        or ledger['calls'][call].get('actual')!=[74291,65536]
        or 'reply' in receipt):
        raise ValueError('Exact settled length receipt changed')
    worker=services.effects.read('worker-'+call)
    if (not worker or 'result' in worker or services.effects.read('apply-'+call) is not None
        or services.tdd.state('TEST-RECORDS').preparation_attempts!=0):
        raise ValueError('Partial output must remain wholly unapplied')
    plan=services.effects.read('code-v54-step4-prepare-TEST-RECORDS')
    for path,encoded in plan['snapshots']['TEST-RECORDS'].items():
        current=(integration/path).read_bytes() if (integration/path).is_file() else None
        expected=bytes.fromhex(encoded) if encoded is not None else None
        if current!=expected:
            raise ValueError('Records source differs from unmodified snapshot')
    workers.authoring_clarifications={'TEST-RECORDS':'\nThe settled prior generation used all 65536 tokens on recursively growing assertion-helper names and emitted no Test/Story markers. That partial response was rejected and NONE was applied. Write the actual 24 mapped Test methods FIRST, before helpers, and use a small finite helper set. Never build chains of wrappers or repeat helper names/suffixes. Use supplied harness/recording examples and real APIs; every assertion must exercise the specified behavior against the prepared stubs. No business implementation, fake expected outcomes or placeholders. Preserve the full acceptance mapping; the strict host hash-bound edit protocol controls serialization.'}
    atomic_write(state,'recovery-authorizations/v54-records-length-reconciled.json',json.dumps({
        'candidate':result['candidate_revision'],'contract_sha256':contract.sha256,
        'failed_call':call,'receipt_sha256':sha256(raw).hexdigest(),
        'settled_usage':[74291,65536],'usage':budget.totals(),
        'retained_uncertain':retained,'partial_applied':False,'human_accepted':False,
        'repair':'Same configured Coder, unchanged completion cap/deadline, test-first finite helpers and existing strict hash-bound transport; actual Judge still required'},indent=2).encode())
    return True
