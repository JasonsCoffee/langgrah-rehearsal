"""Live evidence uses committed bytes, even when native text loading normalizes CRLF."""
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import pytest
sys.path.insert(0,str(Path('openspec/changes/rehearse-monopoly-game-lobby').resolve()))


def test_committed_crlf_body_is_not_silently_normalized(tmp_path):
    from rehearsal_context_reviews import build_review_packet
    def git(*args):return subprocess.check_output(['git','-C',str(tmp_path),*args])
    git('init','-q');git('config','core.autocrlf','false')
    (tmp_path/'Runtime').mkdir();(tmp_path/'specs').mkdir()
    raw=b'class A {\r\n    string X = @"one\r\ntwo";\r\n}\r\n'
    (tmp_path/'Runtime/A.cs').write_bytes(raw);(tmp_path/'specs/spec.md').write_text('Requirement')
    git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
    unit=SimpleNamespace(id='U',role='impl',owns=('Runtime/A.cs',),acceptance=('T',))
    workers=SimpleNamespace(root=tmp_path,contract=SimpleNamespace(sha256='c',spec=SimpleNamespace(path='specs/spec.md'),units=(unit,)),
        services=SimpleNamespace(state={'patches':{'U':{'Runtime/A.cs':'hash'}}}))
    p=build_review_packet(workers,unit,{'Runtime/A.cs':(tmp_path/'Runtime/A.cs').read_text(),
        'specs/spec.md':'Requirement'},{'gate':'compile'},'policy','defect')
    assert next(s for s in p.sources if s.path=='Runtime/A.cs').content.encode()==raw

