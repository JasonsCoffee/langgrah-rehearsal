"""A reuse operation cannot change identity after its provenance is persisted."""
import importlib.util
import json
from pathlib import Path
import pytest


def fixtures():
    p=Path('tests/test_codex_review_reuse.py')
    s=importlib.util.spec_from_file_location('reuse_fixture',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


@pytest.mark.parametrize('bad',['prompt','policy','receipt-proof'])
def test_existing_reuse_identity_cannot_be_overwritten(tmp_path,bad):
    f=fixtures();calls,prompt,_=f.prepare(tmp_path);m=f.helper()
    m.reuse_review(calls,'new-review','TEST-A',prompt,32)
    proof=next((calls.budget.root/'review-reuse').glob('*.json'))
    if bad=='prompt':prompt+=' changed'
    elif bad=='policy':
        from dataclasses import replace
        calls.client.config=replace(calls.client.config,effort='low')
    else:
        d=json.loads(proof.read_bytes());d['receipt_sha256']='changed';proof.write_text(json.dumps(d))
    before=proof.read_bytes()
    with pytest.raises(ValueError):m.reuse_review(calls,'new-review','TEST-A',prompt,32)
    assert proof.read_bytes()==before


def test_identical_reconnect_keeps_original_provenance_bytes(tmp_path):
    f=fixtures();calls,prompt,reply=f.prepare(tmp_path);m=f.helper()
    m.reuse_review(calls,'new-review','TEST-A',prompt,32)
    proof=next((calls.budget.root/'review-reuse').glob('*.json'));before=proof.read_bytes()
    assert m.reuse_review(calls,'new-review','TEST-A',prompt,32)==reply
    assert proof.read_bytes()==before
