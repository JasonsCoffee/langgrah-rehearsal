"""Only hash-bound model edits may restore and repair delegated owned source."""
import importlib.util
from pathlib import Path
import json
from hashlib import sha256
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/impl_anchored_transport.py')
    s=importlib.util.spec_from_file_location('impl_anchored_transport',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fixture():
    path='Runtime/Script/UI/LobbyRehearsal/LobbyShellBindings.cs';base=b'class Shell { void Run() { Old(); } }'
    job={'files':{},'edits':[{'path':path,'base_sha256':sha256(base).hexdigest(),'replacements':[{'old':'Old();','new':'Repaired();'}]}],
         'accept_bases':[path],'reason':'Actual delegated change'}
    return path,base,job


def test_model_authored_edit_applies_to_exact_previously_paid_base():
    path,base,job=fixture();patch=module().admit(json.dumps(job),(path,),{path:base},{path:b'class Shell {}'},(path,))
    assert patch[path]==b'class Shell { void Run() { Repaired(); } }'


@pytest.mark.parametrize('bad',['hash','unowned','no_edit','no_accept','missing_anchor'])
def test_incomplete_or_unproven_impl_edits_cannot_be_admitted(bad):
    path,base,job=fixture()
    if bad=='hash':job['edits'][0]['base_sha256']='0'*64
    if bad=='unowned':job['edits'][0]['path']='Tests/Frozen.cs'
    if bad=='no_edit':job['edits']=[]
    if bad=='no_accept':job['accept_bases']=[]
    if bad=='missing_anchor':job['edits'][0]['replacements'][0]['old']='Invented();'
    with pytest.raises(ValueError):module().admit(json.dumps(job),(path,),{path:base},{path:b'class Shell {}'},(path,))
