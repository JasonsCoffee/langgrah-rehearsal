import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import pytest

def parser():
    spec=importlib.util.spec_from_file_location('anchored_author',Path(__file__).with_name('anchored_author.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.parse_anchored_patch

SOURCE='first stable assertion\nsecond broken assertion\nthird stable assertion\n'
def response():
    return {'files':{'note.md':'accurate map'},'edits':[{'path':'suite.cs','base_sha256':sha256(SOURCE.encode()).hexdigest(),
        'replacements':[{'old':'second broken assertion','new':'second repaired assertion'}]}],'reason':'Repair the delegated assertion'}

def test_unique_delegated_replacement_preserves_every_other_byte():
    files,reason=parser()(json.dumps(response()),('suite.cs','note.md'),{'suite.cs':SOURCE})
    assert files=={'suite.cs':SOURCE.replace('broken','repaired').encode(),'note.md':b'accurate map'}
    assert reason=='Repair the delegated assertion'

@pytest.mark.parametrize('mode',['missing','duplicate','wrong_hash','unowned','full_source','overlap','noop','empty'])
def test_invalid_or_ambiguous_edits_fail_closed(mode):
    data=response();source=SOURCE
    if mode=='missing':data['edits'][0]['replacements'][0]['old']='absent'
    if mode=='duplicate':source+= 'second broken assertion';data['edits'][0]['base_sha256']=sha256(source.encode()).hexdigest()
    if mode=='wrong_hash':data['edits'][0]['base_sha256']='0'*64
    if mode=='unowned':data['edits'][0]['path']='other.cs'
    if mode=='full_source':data['files']['suite.cs']='replace the whole suite'
    if mode=='overlap':data['edits'][0]['replacements'].append({'old':'broken assertion','new':'other'})
    if mode=='noop':data['edits'][0]['replacements'][0]['new']='second broken assertion'
    if mode=='empty':data['edits'][0]['replacements'][0]['old']=''
    with pytest.raises(ValueError):parser()(json.dumps(data),('suite.cs','note.md'),{'suite.cs':source})

def test_replacements_use_original_offsets_without_cascading():
    data=response();data['edits'][0]['replacements']=[{'old':'first stable','new':'second broken'},{'old':'second broken','new':'fixed'}]
    files,_=parser()(json.dumps(data),('suite.cs','note.md'),{'suite.cs':SOURCE})
    assert files['suite.cs']==b'second broken assertion\nfixed assertion\nthird stable assertion\n'

def test_duplicate_json_keys_are_rejected():
    with pytest.raises(ValueError):parser()('{"files":{},"files":{},"edits":[],"reason":"x"}',('suite.cs',),{'suite.cs':SOURCE})
