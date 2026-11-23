"""Cycle-71 approval cannot widen assertion edits or contract ownership."""
from copy import deepcopy
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


@pytest.mark.parametrize('unit,method',[('TEST-PRES-CORE','Story_L1_03'),('TEST-PRES-NFR','Story_NFR_01')])
def test_only_approved_body_can_change(tmp_path,unit,method):
    from approved_test_reconciliation_v71 import SCOPE,validate_patch
    path=SCOPE[unit]['path'];source=tmp_path/path;source.parent.mkdir(parents=True)
    raw=('class T { [Test] void '+method+'() { A(); } void Other() { B(); } }').encode()
    source.write_bytes(raw)
    validate_patch(unit,{path:raw.replace(b'A();',b'C();')},tmp_path)
    for altered in [raw,raw.replace(b'B();',b'C();'),raw.replace(b'[Test]',b'[Ignore]')]:
        with pytest.raises(ValueError):validate_patch(unit,{path:altered},tmp_path)
    with pytest.raises(ValueError):validate_patch(unit,{path:raw.replace(b'A();',b'C();'),'unowned.cs':b''},tmp_path)


def test_revision_retains_ownership_acceptance_and_scheduling():
    from approved_test_reconciliation_v71 import PREVIOUS_SHA,author_paths,validate_revision
    old={'contract_version':70,'units':[{'id':'TEST-PRES-CORE','role':'test','owns':['test.cs'],'instructions':'old','acceptance':['A']},
        {'id':'SHELL','role':'impl','owns':['runtime.cs'],'instructions':'old','depends_on':[]}]}
    new=deepcopy(old);new.update(contract_version=71,previous_contract_sha256=PREVIOUS_SHA)
    new['units'][0]['owns']+=list(author_paths('TEST-PRES-CORE')[1:]);new['units'][0]['instructions']='approved'
    validate_revision(old,new)
    for unit,key,value in [(0,'acceptance',[]),(1,'owns',['test.cs']),(1,'depends_on',['OTHER'])]:
        bad=deepcopy(new);bad['units'][unit][key]=value
        with pytest.raises(ValueError):validate_revision(old,bad)
