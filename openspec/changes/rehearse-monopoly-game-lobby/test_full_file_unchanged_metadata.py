"""Frozen native admission edge: full replies may repeat unchanged metadata."""
from hashlib import sha256
import json
import pytest
import full_file_admission as module
from test_full_file_admission import prepare,OP,UNIT,PATH


@pytest.mark.parametrize('baseline_same',[True,False])
def test_omitted_apply_entry_requires_exact_original_bytes(tmp_path,monkeypatch,baseline_same):
    state,integration,ledger,applied=prepare(tmp_path)
    run=state/'.agent/runs/monopoly-game-lobby';call=OP+'-'+UNIT+'-'+UNIT
    meta=PATH+'.meta';body=b'unchanged original metadata'
    (integration/meta).write_bytes(body)
    worker_path=run/'services-v54/effects'/('worker-'+call+'.json')
    worker=json.loads(worker_path.read_bytes());worker['result']['files'][meta]=body.hex();worker_path.write_text(json.dumps(worker))
    applied['expected'][meta]=sha256(body).hexdigest()
    (run/'services-v54/effects'/('apply-'+call+'.json')).write_text(json.dumps(applied))
    receipt_path=run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json')
    receipt=json.loads(receipt_path.read_bytes());reply=json.loads(receipt['reply']['text']);reply['files'][meta]=body.decode();receipt['reply']['text']=json.dumps(reply);receipt_path.write_text(json.dumps(receipt))
    def read_before(root,*args):
        assert root==integration and args==('show','before:'+meta)
        return body if baseline_same else b'different original metadata'
    monkeypatch.setattr(module,'git',read_before,raising=False)
    if baseline_same:
        proof=module.admitted_full_file(state,54,OP,UNIT,(PATH,meta),'candidate',integration,ledger,'contract')
        assert proof['file_sha256'][meta]==sha256(body).hexdigest()
    else:
        with pytest.raises(ValueError):module.admitted_full_file(state,54,OP,UNIT,(PATH,meta),'candidate',integration,ledger,'contract')
