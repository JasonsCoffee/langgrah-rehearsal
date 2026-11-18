"""Writable aliases must not redirect declared ownership into protected inputs."""
import os
import subprocess

import pytest

from test_contracts import Rules, bundle
from test_workspaces import workspace
from unity_coder.core.ownership import validate_owned_path
from unity_coder.core.execution_host import ExecutionHost


def link_directory(link, target):
    if os.name=='nt':
        subprocess.run(['cmd','/c','mklink','/J',str(link),str(target)],check=True,capture_output=True)
    else:
        link.symlink_to(target,target_is_directory=True)


def test_ownership_rejects_alias_to_protected_directory(tmp_path):
    (tmp_path/'Runtime').mkdir()
    (tmp_path/'specs').mkdir()
    link_directory(tmp_path/'Runtime/alias',tmp_path/'specs')
    with pytest.raises(ValueError):
        validate_owned_path('Runtime/alias/spec.md',('Runtime',),tmp_path,Rules(),())


def test_coding_tool_rejects_alias_created_after_contract_validation(workspace):
    manager,_,base,contract=workspace
    handle=manager.create_unit('U1-state',base,{})
    folder=handle.path/'Runtime/Script/Queue'
    # Only disposable test fixture files are removed to simulate late alias drift.
    for child in folder.iterdir():child.unlink()
    folder.rmdir()
    protected=handle.path/'specs'
    link_directory(folder,protected)
    victim=protected/'DinerState.cs'
    victim.write_bytes(b'protected')
    host=ExecutionHost(handle,contract,Rules())
    with pytest.raises(ValueError):
        host.write_file('Runtime/Script/Queue/DinerState.cs',b'overwrite')
    assert victim.read_bytes()==b'protected'
