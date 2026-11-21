"""Candidate advance preserves unrelated bytes and fails closed on interruption."""
import copy
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_generated_entry_reconciliation import module,fixture


def setup(tmp_path,monkeypatch):
    m=module();host=tmp_path/'host';source=tmp_path/'source';state=tmp_path/'state'
    host.mkdir();source.mkdir();state.mkdir();before,observed=fixture()
    good=b'class Monopoly { public void OnDestroy() {\n#region GeneratedBreak\nContext.Break();\n#endregion\n Guard(); } }'
    shell='Runtime/Script/UI/LobbyRehearsal/Shell.cs';unrelated='Assets/Unrelated.asset'
    for root,path,raw in [(host,m.ENTRY,observed),(host,'Assets/JJGame/monopoly/'+shell,b'old-shell'),
                          (host,unrelated,b'preserve-me'),(source,m.RELATIVE,good),(source,shell,b'new-shell'),
                          (source,'Tests/Frozen.txt',b'frozen')]:
        p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    digest=lambda b:sha256(b).hexdigest()
    managed={m.ENTRY:digest(before),'Assets/JJGame/monopoly/'+shell:digest(b'old-shell')}
    value={'candidate':m.OLD_CANDIDATE,'baseline':{unrelated:digest(b'preserve-me')},'managed':managed,
           'pending':{},'history':{m.OLD_CANDIDATE:copy.deepcopy(managed)},'installing':False}
    class Overlay:
        def __init__(self):self.state=state/'overlay';self.state.mkdir();self.value=copy.deepcopy(value)
        def read(self):
            if self.value['installing']:raise ValueError('Interrupted overlay')
            return copy.deepcopy(self.value)
        def save(self,v):self.value=copy.deepcopy(v)
        def scan(self):return {p.relative_to(host).as_posix():digest(p.read_bytes()) for p in host.rglob('*') if p.is_file()}
        def allowed(self,p):return p in managed
        def entry_exceptions(self):return {m.ENTRY:'original-baseline'}
        def check(self,v):assert self.scan()==v['baseline']|v['managed']|v['pending']
    overlay=Overlay();obj=SimpleNamespace(host=host,state=state,overlay=overlay,preflight=lambda:None)
    proof={'state':'observed','old_candidate':m.OLD_CANDIDATE,'old_entry_sha256':digest(before),
           'observed_entry_sha256':digest(observed),'frozen':{'Tests/Frozen.txt':digest(b'frozen')}}
    (state/Path(m.PROOF).parent).mkdir(parents=True)
    (state/m.PROOF).write_text(json.dumps(proof))
    (state/'recovery-authorizations/generated-entry-v68.observed.bin').write_bytes(observed)
    def git(root,*args):
        if args[:2]==('rev-parse','HEAD'):return b'new-candidate\n'
        if args[0] in ('status','merge-base'):return b''
        if args[0]=='ls-tree':return (m.RELATIVE+'\0'+shell+'\0').encode()
        if args[0]=='show':
            revision,path=args[1].split(':',1)
            return before if revision==m.OLD_CANDIDATE else (source/path).read_bytes()
        raise AssertionError(args)
    monkeypatch.setattr(m,'git',git)
    return m,obj,source,shell,value


def test_admitted_candidate_advance_keeps_baseline_and_old_history(tmp_path,monkeypatch):
    m,host,source,shell,old=setup(tmp_path,monkeypatch)
    m.advance_materialization(host,source,'new-candidate')
    assert (host.host/'Assets/Unrelated.asset').read_bytes()==b'preserve-me'
    assert (host.host/m.ENTRY).read_bytes()==(source/m.RELATIVE).read_bytes()
    assert (host.host/('Assets/JJGame/monopoly/'+shell)).read_bytes()==b'new-shell'
    assert host.overlay.value['candidate']=='new-candidate'
    assert host.overlay.value['history'][m.OLD_CANDIDATE]==old['managed']


def test_unrelated_drift_stops_before_any_candidate_write(tmp_path,monkeypatch):
    m,host,source,shell,old=setup(tmp_path,monkeypatch)
    (host.host/'Assets/Unrelated.asset').write_bytes(b'foreign-change')
    with pytest.raises(ValueError):m.advance_materialization(host,source,'new-candidate')
    assert (host.host/('Assets/JJGame/monopoly/'+shell)).read_bytes()==b'old-shell'
    assert host.overlay.value==old


def test_missing_generated_lifecycle_stops_before_any_candidate_write(tmp_path,monkeypatch):
    m,host,source,shell,old=setup(tmp_path,monkeypatch)
    p=source/m.RELATIVE;p.write_bytes(p.read_bytes().replace(b'Context.Break();',b'Guard();'))
    with pytest.raises(ValueError):m.advance_materialization(host,source,'new-candidate')
    assert host.overlay.value==old


def test_partial_write_never_publishes_a_verified_candidate(tmp_path,monkeypatch):
    m,host,source,shell,old=setup(tmp_path,monkeypatch);write=m.atomic_write
    def interrupt(root,path,raw):
        if root==host.host and path.endswith('/Shell.cs'):raise OSError('simulated interruption')
        write(root,path,raw)
    monkeypatch.setattr(m,'atomic_write',interrupt)
    with pytest.raises(OSError):m.advance_materialization(host,source,'new-candidate')
    assert host.overlay.value['installing'] is True
    assert host.overlay.value['candidate']==m.OLD_CANDIDATE
    assert 'new-candidate' not in host.overlay.value['history']
    with pytest.raises(ValueError):host.overlay.read()
