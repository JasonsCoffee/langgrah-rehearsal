"""Frozen token-bound amendments retain all stopped-run accounting."""
from dataclasses import asdict
import json
import pytest
from test_abandoned_recovery import stopped, recover
from test_architect_boundary import planning
from test_contracts import bundle


def token_case(stopped, *, input_limit=200, output_limit=100, max_cycles=3):
    from unity_coder.core.recovery import TokenRecoveryGrant
    b,current,context,budget,lease,grant=stopped
    path=b.state_root/budget.path
    data=json.loads(path.read_bytes()); data['limits'][2]=3
    budget.limits[2]=3
    path.write_text(json.dumps(data,sort_keys=True))
    values=asdict(grant)|dict(max_cycles=max_cycles,input_limit=input_limit,output_limit=output_limit)
    return (*stopped[:5],TokenRecoveryGrant(**values))


def test_token_reservation_stop_can_recover_without_cycle_ceiling_growth(stopped):
    case=token_case(stopped)
    b,_,_,budget,_,_=case
    before=json.loads((b.state_root/budget.path).read_bytes())
    recover(case)
    after=json.loads((b.state_root/budget.path).read_bytes())
    assert after['limits']==[200,100,3,2]
    assert after['calls']==before['calls'] and after['cycles']['1']==before['cycles']['1']
    assert budget.totals()==(25,10) and 'stopped' not in after
    audit=json.loads((b.state_root/b.prefix/'recoveries/recovery-1.json').read_bytes())
    assert audit['authorization']['input_limit']==200
    assert json.loads(bytes.fromhex(audit['saved']['budget.json']))==before


@pytest.mark.parametrize('input_limit,output_limit,max_cycles',[
    (99,100,3),(200,49,3),(True,100,3),(200,False,3),(0,100,3),
    (200,-1,3),(100,50,3),(200,100,2)])
def test_amendment_rejects_shrinking_invalid_or_unchanged_bounds(stopped,input_limit,output_limit,max_cycles):
    case=token_case(stopped,input_limit=input_limit,output_limit=output_limit,max_cycles=max_cycles)
    before=(case[0].state_root/case[3].path).read_bytes()
    with pytest.raises(ValueError):recover(case)
    assert (case[0].state_root/case[3].path).read_bytes()==before


def test_actual_overruns_are_preserved_and_need_greater_new_allowance(stopped):
    case=token_case(stopped)
    b,_,_,budget,_,_=case
    budget.reconcile('uncertain-old-call',150,60)
    recover(case)
    assert budget.totals()==(150,60)
    assert json.loads((b.state_root/budget.path).read_bytes())['calls']['uncertain-old-call']['actual']==[150,60]


def test_new_token_bounds_must_leave_room_for_dispatch(stopped):
    case=token_case(stopped)
    case[3].reconcile('uncertain-old-call',200,100)
    with pytest.raises(ValueError):recover(case)


def test_interrupted_token_amendment_reuses_exact_intent(stopped,monkeypatch):
    import unity_coder.core.recovery as module
    case=token_case(stopped)
    original=module.atomic_write
    def fail(root,path,content):
        if '/recoveries/' in path and json.loads(content).get('state')=='complete':
            raise OSError('crash after publication')
        original(root,path,content)
    monkeypatch.setattr(module,'atomic_write',fail)
    with pytest.raises(OSError):recover(case)
    monkeypatch.setattr(module,'atomic_write',original)
    recover(case)
    assert case[3].totals()==(25,10) and case[3].limits==[200,100,3,2]
