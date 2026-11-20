"""Frozen exact-admission checks for full-file zero-HTTP recovery."""
import json
from hashlib import sha256
from pathlib import Path
import pytest
from full_file_admission import admitted_full_file

OP='v54-step2-prepare'
UNIT='TEST-CHAT-STATE'
PATH='Tests/Runtime/Script/LobbyRehearsal/LobbyChatStateTests.cs'

def prepare(tmp_path):
    state=tmp_path/'state';integration=tmp_path/'integration'
    file=integration/PATH;file.parent.mkdir(parents=True);file.write_bytes(b'actual coder source')
    encoded={PATH:file.read_bytes().hex()};body={'files':{PATH:'actual coder source'},'reason':'authored'}
    run=state/'.agent/runs/monopoly-game-lobby';effects=run/'services-v54/effects';effects.mkdir(parents=True)
    call=OP+'-'+UNIT+'-'+UNIT
    worker={'identity':{'base':'before','stage':'test_authoring','unit':UNIT},'result':{'files':encoded,'reason':'authored'}}
    apply={'before':'before','after':'candidate','identity':{'base':'before','unit':UNIT,'changes':encoded,'contract':'contract'},'expected':{PATH:sha256(file.read_bytes()).hexdigest()}}
    (effects/('worker-'+call+'.json')).write_text(json.dumps(worker))
    (effects/('apply-'+call+'.json')).write_text(json.dumps(apply))
    records=run/'model-calls';records.mkdir()
    receipt={'identity':{'call_id':call,'unit_id':UNIT,'role':'coder','model':'deepseek/deepseek-v4.1-flash'},'reply':{'text':json.dumps(body),'input_tokens':100,'output_tokens':20}}
    (records/(sha256(call.encode()).hexdigest()+'.json')).write_text(json.dumps(receipt))
    ledger={'calls':{call:{'actual':[100,20],'reserved':[200,65536],'unit':UNIT,'version':54}}}
    return state,integration,ledger,apply

def test_exact_full_file_admission_is_reusable(tmp_path):
    state,integration,ledger,_=prepare(tmp_path)
    proof=admitted_full_file(state,54,OP,UNIT,(PATH,),'candidate',integration,ledger,'contract')
    assert proof['file_sha256']=={PATH:sha256(b'actual coder source').hexdigest()}
    assert proof['actual_calls']==[OP+'-'+UNIT+'-'+UNIT]

@pytest.mark.parametrize('change',['source','unsettled','ownership','apply','reply'])
def test_full_file_admission_rejects_changed_or_unadmitted_effects(tmp_path,change):
    state,integration,ledger,apply=prepare(tmp_path);owns=(PATH,)
    call=OP+'-'+UNIT+'-'+UNIT
    run=state/'.agent/runs/monopoly-game-lobby'
    if change=='source':(integration/PATH).write_bytes(b'changed')
    if change=='unsettled':del ledger['calls'][call]['actual']
    if change=='ownership':owns=('Other.cs',)
    if change=='apply':
        apply['after']='other';(run/'services-v54/effects'/('apply-'+call+'.json')).write_text(json.dumps(apply))
    if change=='reply':
        p=run/'model-calls'/(sha256(call.encode()).hexdigest()+'.json');d=json.loads(p.read_bytes());d['reply']['text']='{"files":{},"reason":"not applied"}';p.write_text(json.dumps(d))
    with pytest.raises(ValueError):
        admitted_full_file(state,54,OP,UNIT,owns,'candidate',integration,ledger,'contract')
