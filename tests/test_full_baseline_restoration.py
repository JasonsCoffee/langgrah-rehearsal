"""Restoration uses exact prior blobs and genuine positive reviews only."""
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/full_baseline_restoration.py')
    s=importlib.util.spec_from_file_location('full_baseline_restoration',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def test_exact_owned_baseline_blobs_only():
    assert module().restoration_changes({'SHELL':['Runtime/Script/A.cs']},
        {'Runtime/Script/A.cs':b'proven stub'},{'Tests/T.cs':'frozen'})=={'SHELL':{'Runtime/Script/A.cs':b'proven stub'}}


@pytest.mark.parametrize('path',['Tests/T.cs','../escape.cs'])
def test_no_test_or_external_restoration(path):
    with pytest.raises(ValueError):module().restoration_changes({'SHELL':[path]},{path:b'value'},{'Tests/T.cs':'frozen'})


def test_genuine_positive_review_required():
    decision={'valid':True,'explanation':'real coverage review'};text=json.dumps(decision)
    receipt={'identity':{'model':'gpt-6.1-sol','effort':'medium'},'reply':{'model':'gpt-6.1-sol','text':text,'input_tokens':10,'output_tokens':2}}
    sdk={'text':text,'input_tokens':10,'output_tokens':2}
    assert module().positive_review(receipt,sdk,{'actual':[10,2]},'real coverage review')=='real coverage review'
    bad=receipt|{'reply':receipt['reply']|{'text':json.dumps(decision|{'valid':False})}}
    with pytest.raises(ValueError):module().positive_review(bad,sdk,{'actual':[10,2]},'real coverage review')
