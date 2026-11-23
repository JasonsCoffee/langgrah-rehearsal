"""Only real negative review of completely frozen ownership permits early rework."""
from pathlib import Path
import sys
import json
from hashlib import sha256
from types import SimpleNamespace
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_only_negative_completely_frozen_scope_is_eligible():
    from frozen_scope_review import eligible
    negative={'valid':False,'explanation':'Actual invalid source'}
    assert eligible(('Tests/A.cs',),{'Tests/A.cs':'h'},1,negative)
    assert not eligible(('Tests/A.cs','new-note.md'),{'Tests/A.cs':'h'},1,negative)
    assert not eligible(('Tests/A.cs',),{'Tests/A.cs':'h'},0,negative)
    assert not eligible(('Tests/A.cs',),{'Tests/A.cs':'h'},1,{'valid':True,'explanation':'valid'})
    assert not eligible((),{},1,negative)
    assert not eligible(('Tests/A.cs',),{'Tests/A.cs':'h'},1,{'valid':False,'explanation':''})


@pytest.mark.parametrize('bad',[None,'charge','instructions'])
def test_route_requires_settled_current_evidence_and_only_returns_rework(tmp_path,monkeypatch,bad):
    from frozen_scope_review import FrozenScopeServices
    from evidence_packet import make_packet
    from unity_coder.core.executor import StepResult
    import unity_coder.core.workspaces
    monkeypatch.setattr(unity_coder.core.workspaces,'git',lambda *args:b'candidate\n')
    def write(path,value):
        p=tmp_path/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8')
    unit=SimpleNamespace(id='TEST-U',role='test',owns=('Tests/A.cs',),spec_ref='C',instructions='Exact contract')
    module=tmp_path/'module';(module/'Tests').mkdir(parents=True);(module/'Tests/A.cs').write_bytes(b'test')
    prefix='.agent/runs/monopoly-game-lobby/services-v73'
    operation='v73-step1-prepare-review-TEST-U';key=sha256(operation.encode()).hexdigest()
    decision={'valid':False,'explanation':'Invalid source'};feedback='Independent Judge findings for TEST-U: Invalid source'
    packet=make_packet({'run':'monopoly-game-lobby','contract':'contract','candidate':'candidate','unit':'TEST-U',
        'stage':'test_review','policy':'policy'},(),(),{'unit_instructions':'Wrong' if bad=='instructions' else 'Exact contract'}, {},(), 'spec')
    p=tmp_path/'context-packets'/packet.canonical_sha256/'canonical.json';p.parent.mkdir(parents=True);p.write_bytes(packet.canonical_input.encode())
    write(prefix+'/effects/review-v73-step1-prepare-TEST-U.json',{'identity':{'unit':'TEST-U'},'result':{'rejected':feedback}})
    write('context-verdicts/'+sha256(operation.encode()).hexdigest()+'.json',{'candidate':'candidate','operation':operation,
        'policy':'policy','decision':decision,'canonical_sha256':packet.canonical_sha256,'final_call':operation})
    write('.agent/runs/monopoly-game-lobby/model-calls/'+key+'.json',{'identity':{'role':'judge','model':'gpt-6.1-sol','effort':'low','backend_policy_sha256':'policy'},'reply':{'text':json.dumps(decision)}})
    write('codex-receipts/'+key+'.json',{'text':json.dumps(decision),'policy_sha256':'policy','input_tokens':10,'output_tokens':2})
    recorded=[]
    def rework(findings,reason):
        recorded.extend(findings)
        return StepResult('ended',{}, {'outcome':'rework'})
    retired=SimpleNamespace(id='RETIRED',role='test',status='retired')
    def tdd_state(identity):
        assert identity!='RETIRED', 'Retired units have no active TDD state'
        return SimpleNamespace(preparation_attempts=1)
    inner=SimpleNamespace(root=tmp_path,prefix=prefix,contract=SimpleNamespace(contract_version=73,sha256='contract',units=(retired,unit)),
        integration=SimpleNamespace(path=module),state={'feedback':feedback},tdd=SimpleNamespace(frozen=False,state=tdd_state),
        workers=SimpleNamespace(context_reviews=SimpleNamespace(policy='policy')),budget=SimpleNamespace(_read=lambda:{'calls':{operation:{'actual':[0,0] if bad=='charge' else [10,2]}}}),
        preflight=lambda:None,_save=lambda:None,_contract_rework=rework,
        step=lambda *_:pytest.fail('Unchanged frozen source must not be retried'))
    services=FrozenScopeServices(inner,tmp_path,{'Tests/A.cs':sha256(b'test').hexdigest()})
    if bad:
        with pytest.raises(ValueError):services.step('prepare','v73-step2-prepare')
        assert not recorded
    else:
        report=services.step('prepare','v73-step2-prepare')
        assert report.result=={'outcome':'rework'} and recorded[0].defect_class=='contract'
        assert (module/'Tests/A.cs').read_bytes()==b'test'
        assert services.reconcile('prepare','v73-step2-prepare')==report
