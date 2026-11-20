"""Bounded host recovery only for natively settled zero-HTTP review failures."""
from hashlib import sha256
import json
import time
from pathlib import Path
from operational_transport import retained_run_reservations, retained_transport_failure,retained_key_limit_failure,retained_calibration_failure,retained_tls_probe_failure,retained_sol_review_failure,retained_coder_connection_failure
from unity_coder.core.storage import atomic_write
from unity_coder.core.workspaces import git


def zero_http_review_unit(receipt: dict, charge: dict, operation: str, model: str) -> str:
    identity=receipt.get('identity',{});unit=identity.get('unit_id')
    if (not isinstance(unit,str) or identity.get('call_id')!=operation+'-review-'+unit
        or identity.get('role')!='judge' or identity.get('model')!=model or 'reply' in receipt
        or receipt.get('failure')!={'transport':'direct_preconnect','phase':'tls_establishment',
            'failure_kind':'tls','input_tokens':0,'output_tokens':0}
        or charge.get('actual')!=[0,0] or charge.get('unit')!=unit):
        raise ValueError('Not a proven zero-HTTP review failure')
    return unit


def zero_http_coder_unit(receipt: dict, charge: dict, operation: str, model: str) -> str:
    identity=receipt.get('identity',{});unit=identity.get('unit_id')
    base=operation+'-'+str(unit)+'-'+str(unit)
    if (not isinstance(unit,str) or identity.get('call_id') not in (base,base+'-anchor-format-1')
        or identity.get('role')!='coder' or identity.get('model')!=model or 'reply' in receipt
        or receipt.get('failure')!={'transport':'direct_preconnect','phase':'tls_establishment',
            'failure_kind':'tls','input_tokens':0,'output_tokens':0}
        or charge.get('actual')!=[0,0] or charge.get('unit')!=unit):
        raise ValueError('Not a proven zero-HTTP coder failure')
    return unit


def recover_zero_http(state,contract,budget,services,integration,settings,executor,workers) -> bool:
    run=state/'.agent/runs/monopoly-game-lobby'
    result_path=run/'result.json'
    if not result_path.exists():return False
    result=json.loads(result_path.read_bytes())
    if result.get('outcome')!='operational' or executor.stage()!='ended':return False
    saved=json.loads((run/('executor-v'+str(contract.contract_version)+'.json')).read_bytes())
    last=saved['steps'][-1];operation=last['operation_id']
    if last['stage']!='prepare' or services.tdd.frozen:return False
    ledger=budget._read();records=run/'model-calls';found=[]
    for call_id,charge in ledger['calls'].items():
        if not call_id.startswith(operation+'-'):continue
        receipt=json.loads((records/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes())
        try:unit=zero_http_review_unit(receipt,charge,operation,settings.judge.model);kind='review'
        except ValueError:
            try:unit=zero_http_coder_unit(receipt,charge,operation,settings.coder.model);kind='coder'
            except ValueError:continue
        found.append((call_id,unit,receipt,kind))
    if len(found)!=1:return False
    call_id,unit_id,receipt,kind=found[0]

    def reconcile():
        transaction=services.effects.read('transaction')
        if (result.get('contract_sha256')!=contract.sha256
            or git(integration,'rev-parse','HEAD').decode().strip()!=result['candidate_revision']
            or git(integration,'status','--porcelain')
            or not transaction.get('complete') or transaction.get('operation')!=operation
            or settings.judge.model!='openai/gpt-6.1-sol'
            or settings.coder.model!='deepseek/deepseek-v4.1-flash'):
            raise ValueError('Zero-HTTP recovery effects changed')
        retained=retained_run_reservations(state,ledger)
        unit=next(u for u in contract.units if u.id==unit_id)
        if unit.role!='test':raise ValueError('Zero-HTTP preparation recovery requires a test author')
        reuse=None
        if kind=='review' and services.tdd.state(unit_id).preparation_attempts:
            # Reuse only actual model-authored/admitted source, never a verdict.
            matches=[]
            for path in (state/'anchored-author').glob('v'+str(contract.contract_version)+'-*.complete.json'):
                proof=json.loads(path.read_bytes())
                if proof.get('unit')!=unit_id or proof.get('contract_sha256')!=contract.sha256:continue
                if all(sha256((integration/p).read_bytes()).hexdigest()==h for p,h in proof['file_sha256'].items()):matches.append(proof)
            if not matches:
                from full_file_admission import admitted_full_file
                proof=admitted_full_file(state,contract.contract_version,operation,unit_id,
                    tuple(unit.owns),result['candidate_revision'],integration,ledger,contract.sha256)
                matches.append(proof)
            reuse={'unit':unit_id,'operation':'v'+str(contract.contract_version)+'-step'+str(len(saved['steps'])+1)+'-prepare-'+unit_id+'-'+unit_id,
                'hashes':{p:sha256((integration/p).read_bytes()).hexdigest() for p in unit.owns},
                'admitted_proof':matches[-1]}
        workers.zero_http_reuse=reuse
        atomic_write(state,'recovery-authorizations/zero-http/'+operation+'.json',json.dumps({
            'contract_sha256':contract.sha256,'candidate':result['candidate_revision'],
            'failed_call':call_id,'receipt_sha256':sha256((records/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()).hexdigest(),
            'failed_stage':kind,
            'usage':budget.totals(),'retained_uncertain':retained,'reuse':reuse,
            'config_sha256':sha256(Path('ai.local.toml').read_bytes()).hexdigest(),
            'human_accepted':False,'automatic_paid_request_retry':False},indent=2).encode())
        return True
    time.sleep(3)
    executor.resume_operational(reconcile=reconcile)
    executor.advance(executor.stage())
    return True
