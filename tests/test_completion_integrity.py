"""Corrupted recovery records cannot publish unapproved metadata."""
import json
import pytest
from test_contracts import bundle
from test_workspaces import workspace, git
from test_completion import prepare
from unity_coder.core.completion import CandidateCompletion


def test_conflicting_completion_blob_is_rejected_before_ref_update(workspace,tmp_path,monkeypatch):
    c,r,e,w,repo,base=prepare(workspace,tmp_path)
    def fail(before,after): raise OSError('before publication')
    monkeypatch.setattr(c,'_publish',fail)
    with pytest.raises(OSError): c.complete(r,e)
    path=c.review.root/c.path
    intent=json.loads(path.read_bytes())
    intent['after']=c._build(base,b'unapproved metadata',True)
    path.write_text(json.dumps(intent))
    with pytest.raises(ValueError): CandidateCompletion(c.manager,w,c.review).complete(r,e)
    assert git(w.path,'rev-parse','HEAD')==base
