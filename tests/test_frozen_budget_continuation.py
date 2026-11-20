"""A token grant cannot thaw test bytes or change the model policy."""
from hashlib import sha256
import importlib.util
from pathlib import Path
import pytest


def module():
    spec=importlib.util.spec_from_file_location('frozen_budget_continuation',Path('openspec/changes/rehearse-monopoly-game-lobby/frozen_budget_continuation.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def test_physical_frozen_bytes_are_checked_before_new_cycle(tmp_path):
    p=tmp_path/'Tests/A.cs';p.parent.mkdir();p.write_bytes(b'frozen')
    hashes={'Tests/A.cs':sha256(b'frozen').hexdigest()}
    assert module().check_frozen_sources(tmp_path,hashes)==('Tests/A.cs',)
    p.write_bytes(b'changed')
    with pytest.raises(ValueError):module().check_frozen_sources(tmp_path,hashes)


def test_consecutive_budget_contract_may_only_change_cycle_identity():
    old={'contract_version':63,'previous_contract_sha256':'old','units':[{'id':'SHELL','owns':['A.cs']}],'ownership_migrations':[]}
    new=old|{'contract_version':64,'previous_contract_sha256':'digest'}
    module().check_contract_continuity(old,new,'digest')
    changed=new|{'units':[{'id':'SHELL','owns':['Tests/A.cs']}]}
    with pytest.raises(ValueError):module().check_contract_continuity(old,changed,'digest')


def test_frozen_scope_cannot_escape_module(tmp_path):
    with pytest.raises(ValueError):module().check_frozen_sources(tmp_path,{'../escape':'digest'})
