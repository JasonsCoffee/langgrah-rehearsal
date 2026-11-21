"""An unchanged complete peer must not be forced to edit unrelated code."""
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    path=Path('openspec/changes/rehearse-monopoly-game-lobby/impl_anchored_transport.py')
    spec=importlib.util.spec_from_file_location('impl_peer_noop',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def test_explicit_peer_blocked_noop_keeps_exact_complete_source():
    path='Runtime/Script/Shell.cs';current={path:b'class Shell {}'}
    reply=json.dumps({'files':{},'edits':[],'accept_bases':[],'reason':'Only peer ECON has a current compiler error.'})
    assert module().admit(reply,(path,),current,current,(),allow_noop=True)=={}


@pytest.mark.parametrize('bad',['unproven','changed_base','blank_reason'])
def test_noop_cannot_hide_unproven_or_changed_source(bad):
    path='Runtime/Script/Shell.cs';current={path:b'class Shell {}'};bases=dict(current)
    data={'files':{},'edits':[],'accept_bases':[],'reason':'Peer blocked'}
    if bad=='changed_base':bases[path]=b'class Different {}'
    if bad=='blank_reason':data['reason']=''
    with pytest.raises(ValueError):module().admit(json.dumps(data),(path,),bases,current,(),allow_noop=bad!='unproven')
