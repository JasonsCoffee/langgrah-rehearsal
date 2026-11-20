"""Validate actual paid full-file source through native worker/apply receipts."""
from hashlib import sha256
import json
from pathlib import Path
from unity_coder.core.workspaces import git


def admitted_full_file(state: Path, version: int, operation: str, unit: str,
        owns: tuple[str,...], candidate: str, integration: Path, ledger: dict,
        contract_sha256: str) -> dict:
    run=state/'.agent/runs/monopoly-game-lobby'
    call=operation+'-'+unit+'-'+unit
    effects=run/('services-v'+str(version))/'effects'
    worker_path=effects/('worker-'+call+'.json')
    apply_path=effects/('apply-'+call+'.json')
    worker_raw=worker_path.read_bytes();apply_raw=apply_path.read_bytes()
    worker=json.loads(worker_raw);applied=json.loads(apply_raw)
    identity=worker['identity'];result=worker['result'];files=result['files']
    if (identity!={'base':applied['before'],'stage':'test_authoring','unit':unit}
        or applied['after']!=candidate or applied['identity']['base']!=applied['before']
        or applied['identity']['unit']!=unit or applied['identity']['contract']!=contract_sha256
        or not isinstance(files,dict) or not files or not set(files).issubset(owns)
        or not any(p.endswith('.cs') for p in applied['identity']['changes'])
        or not set(applied['identity']['changes']).issubset(files)
        or any(files[p]!=body for p,body in applied['identity']['changes'].items())):
        raise ValueError('Full-file worker/apply identity changed')
    hashes={}
    for path,encoded in files.items():
        if not isinstance(encoded,str):raise ValueError('Invalid native file bytes')
        body=bytes.fromhex(encoded);digest=sha256(body).hexdigest()
        if path not in applied['identity']['changes']:
            if git(integration,'show',applied['before']+':'+path)!=body:
                raise ValueError('Omitted native apply entry was not unchanged original content')
        if (integration/path).read_bytes()!=body or applied['expected'].get(path)!=digest:
            raise ValueError('Admitted full-file bytes changed')
        hashes[path]=digest
    matches=[]
    for call_id,charge in ledger['calls'].items():
        if not (call_id==call or call_id.startswith(call+'-')):continue
        raw=(run/'model-calls'/(sha256(call_id.encode()).hexdigest()+'.json')).read_bytes()
        receipt=json.loads(raw);source=receipt.get('reply');model=receipt['identity']
        if not source:continue
        if (model.get('call_id')!=call_id or model.get('role')!='coder'
            or model.get('unit_id')!=unit or model.get('model')!='deepseek/deepseek-v4.1-flash'
            or charge.get('actual')!=[source['input_tokens'],source['output_tokens']]
            or charge.get('unit')!=unit or charge.get('version')!=version):continue
        try:patch=json.loads(source['text'])
        except ValueError:continue
        if (isinstance(patch,dict) and isinstance(patch.get('files'),dict)
            and all(isinstance(p,str) and isinstance(v,str) for p,v in patch['files'].items())
            and {p:v.encode('utf-8').hex() for p,v in patch['files'].items()}==files
            and patch.get('reason')==result['reason']):
            matches.append({'call_id':call_id,'receipt_sha256':sha256(raw).hexdigest()})
    if len(matches)!=1:raise ValueError('No unique settled paid response matches native admission')
    return {'transport':'native_full_file','unit':unit,'contract_sha256':contract_sha256,
        'file_sha256':hashes,'actual_calls':[m['call_id'] for m in matches],
        'paid_receipts':matches,'worker_sha256':sha256(worker_raw).hexdigest(),
        'apply_sha256':sha256(apply_raw).hexdigest(),'candidate':candidate,
        'human_accepted':False}
