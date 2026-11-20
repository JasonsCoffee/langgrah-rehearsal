"""Compiler paths identify repair owners; unknown/global errors remain shared."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/compile_repair_context.py')
    s=importlib.util.spec_from_file_location('compile_repair_context',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def test_all_diagnostics_must_have_declared_owners():
    contract=SimpleNamespace(owner_of=lambda p:{'Runtime/A.cs':'SHELL'}.get(p))
    assert module().compile_owners(contract,[{'file':'Assets/JJGame/monopoly/Runtime/A.cs'}])==('SHELL',)
    assert module().compile_owners(contract,[{'file':'Assets/JJGame/monopoly/Runtime/A.cs'},{'file':''}]) is None
    assert module().compile_owners(contract,[{'file':'Assets/Other/A.cs'}]) is None


def test_actual_messages_and_snapshot_are_supplied_to_coder():
    state={'verification':{'gate':'compile','status':'failed','request':{'contract_sha256':'same','candidate_revision':'failed-snapshot'},
        'violations':[{'file':'Runtime/A.cs','message':'JJCK0005 actual compiler error'}]}}
    value=module().mechanical_feedback(state,'same')
    assert 'JJCK0005 actual compiler error' in value and 'failed-snapshot' in value
    assert module().mechanical_feedback(state,'different')==''
