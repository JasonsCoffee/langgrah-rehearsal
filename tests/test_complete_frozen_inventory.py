"""Consecutive repair must carry the complete declared frozen inventory."""
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/frozen_implementation_rework.py')
    spec=importlib.util.spec_from_file_location('complete_frozen_inventory',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def inventory():
    contract={'units':[{'id':'TEST','role':'test','status':'active','owns':['Tests/A.cs','Tests/A.cs.meta']},
        {'id':'IMPL','role':'impl','status':'active','owns':['Runtime/Implementation.cs']}]}
    frozen={p:'a'*64 for p in ('Tests/A.cs','Tests/A.cs.meta',
        'Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef',
        'Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef.meta')}
    return contract,frozen


def test_inventory_is_derived_from_frozen_contract_not_historical_count():
    contract,frozen=inventory()
    module().complete_inventory(contract,frozen,frozen)


@pytest.mark.parametrize('mutation',['missing_test','missing_config','extra_runtime','hash_changed','partial_prior'])
def test_missing_extra_or_changed_frozen_sources_fail_closed(mutation):
    contract,prior=inventory();current=dict(prior)
    if mutation=='missing_test':current.pop('Tests/A.cs')
    if mutation=='missing_config':current.pop('Tests/Runtime/Script/jj.Monopoly.Tests.Runtime.asmdef')
    if mutation=='extra_runtime':current['Runtime/Implementation.cs']='b'*64
    if mutation=='hash_changed':current['Tests/A.cs']='b'*64
    if mutation=='partial_prior':
        prior.pop('Tests/A.cs');current.pop('Tests/A.cs')
    with pytest.raises(ValueError):module().complete_inventory(contract,prior,current)
