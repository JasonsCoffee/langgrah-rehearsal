"""Frozen grant and inventory checks for the user's aggregate doubling."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/doubled_budget_continuation.py')
    s=importlib.util.spec_from_file_location('doubled_budget_continuation',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fixture():
    before={'limits':[125000000,12000000,80,2],'calls':{'old':{'reserved':[100,20]}},'cycles':{'66':{'sha256':'old'}}}
    after=json.loads(json.dumps(before));after['limits']=[250000000,24000000,160,2]
    intent={'state':'complete','saved':{'budget.json':json.dumps(before).encode().hex()},'budget_after':after,
            'authorization':{'input_limit':250000000,'output_limit':24000000,'max_cycles':160}}
    approval={'reply':'Double those ceilings','authority':'explicit_user_session','limits':after['limits']}
    return before,after,intent,approval


def test_doubling_preserves_every_old_charge_and_cycle():
    before,after,intent,approval=fixture()
    assert module().validate_grant(intent,approval,after)==before


@pytest.mark.parametrize('bad',['approval','charge','cycle','pending'])
def test_changed_authority_or_history_is_rejected(bad):
    before,after,intent,approval=fixture()
    if bad=='approval':approval['reply']='pending'
    if bad=='charge':after['calls']['old']['reserved'][0]=0
    if bad=='cycle':after['cycles']['66']['sha256']='changed'
    if bad=='pending':intent['state']='pending'
    with pytest.raises(ValueError):module().validate_grant(intent,approval,after)


def test_complete_189_inventory_is_required():
    frozen={f'Tests/{i}.cs':str(i) for i in range(189)}
    old=json.dumps({'tdd':{'frozen':frozen}}).encode()
    manifest={'previous_services_sha256':sha256(old).hexdigest(),'frozen':frozen}
    assert module().frozen_inventory(old,manifest)==frozen
    manifest['frozen']=dict(list(frozen.items())[:-4])
    with pytest.raises(ValueError):module().frozen_inventory(old,manifest)
