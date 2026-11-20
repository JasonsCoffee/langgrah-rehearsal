"""Frozen checks for the two completed non-mutating TLS calibration failures."""
from hashlib import sha256
import json
import pytest
import operational_transport


@pytest.mark.parametrize('case',['429','connection','actual','model'])
def test_exact_tls_probe_reservations_remain_charged(tmp_path,case):
    call='tls-recovery-v23-glm-json-review' if case=='429' else 'tls-recovery-v23-glm-json-review-retry1'
    failure={'http_status':429,'retry_after_seconds':2,'provider_name':'Wafer','limit_source':'upstream_provider_shared_pool'} if case=='429' else {}
    receipt={'identity':{'call_id':call,'role':'judge','unit_id':'TEST-VIP','model':'z-ai/glm-5.3-flash','output_limit':32768},'failure':failure}
    if case=='model':receipt['identity']['model']='other-model'
    reservation={'reserved':[1200,32768]}
    if case=='actual':reservation['actual']=[0,0]
    raw=json.dumps(receipt).encode();folder=tmp_path/'.agent/runs/monopoly-game-lobby/model-calls';folder.mkdir(parents=True)
    (folder/(sha256(call.encode()).hexdigest()+'.json')).write_bytes(raw)
    manifest={'non_mutating_calibration':True,'usage_unknown_retained':True,'calls':{call:{'receipt_sha256':sha256(raw).hexdigest(),'reservation':reservation}}}
    auth=tmp_path/'model-authorizations';auth.mkdir();(auth/'tls-probe-reservations-v23.json').write_text(json.dumps(manifest))
    invoke=lambda:operational_transport.retained_tls_probe_failure(tmp_path,call,receipt,reservation)
    if case in ('429','connection'):assert invoke()==(1200,32768)
    else:
        with pytest.raises(ValueError):invoke()
