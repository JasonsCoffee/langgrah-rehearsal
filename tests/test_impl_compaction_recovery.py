"""Only the inspected rejected compaction may enter this operational recovery."""
from test_implementation_context_scope import module
import pytest


def fixture():
    result={'contract_version':67,'contract_sha256':'013c774cf990ebacc14e4cb4fcbddf954bb3aadb5ce2abfdd9885d7dc29e3783','outcome':'operational','candidate_revision':'1864d5b240a6ccfe36e8ba06fabdbb6f076c206b'}
    transaction={'operation':'v67-step3-code','stage':'code','complete':True}
    failure={'protocol_phase':'item_validation','item_type':'contextCompaction','event_method':'item/started'}
    charge={'reserved':[6251091,65536],'unit':'SHELL','version':67}
    return result,transaction,failure,charge


def test_inspected_failed_effect_can_be_reconciled_without_refund():
    args=fixture();assert module().validate_stop(*args) is None
    assert args[3]['reserved']==[6251091,65536]


@pytest.mark.parametrize('bad',['type','charge'])
def test_different_effect_or_charge_is_not_silently_recovered(bad):
    result,tx,failure,charge=fixture()
    if bad=='type':failure['item_type']='commandExecution'
    else:charge['reserved'][0]=0
    with pytest.raises(ValueError):module().validate_stop(result,tx,failure,charge)
