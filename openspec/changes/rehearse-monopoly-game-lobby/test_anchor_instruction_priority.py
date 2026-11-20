"""Frozen check: actual edit transport follows historical full-file hints."""
from hashlib import sha256
import json
from types import SimpleNamespace
from lobby_production_host import ContextWorkers


def test_final_transport_supersedes_earlier_hints_and_lists_missing_files(tmp_path):
    source='class C { int M() { return 1; } }';(tmp_path/'Code.cs').write_text(source)
    seen=[]
    class Coder:
        calls=SimpleNamespace(budget=SimpleNamespace(root=tmp_path))
        def generate(self,call,unit,prompt,*,max_output_tokens):
            seen.append(json.loads(prompt.partition('\n')[2]))
            return SimpleNamespace(text=json.dumps({'files':{},'edits':[{'path':'Code.cs',
                'base_sha256':sha256(source.encode()).hexdigest(),'replacements':[{'old':'return 1;','new':'return 2;'}]}],'reason':'actual delegated edit'}))
    worker=ContextWorkers(SimpleNamespace(sha256='a'*64,contract_version=29),Coder(),None,tmp_path)
    worker.services=SimpleNamespace(tdd=SimpleNamespace(frozen=None))
    unit=SimpleNamespace(role='test',id='TEST-SOCIAL',owns=('Code.cs',),acceptance=('T',),instructions='Historical hint: return full C# files.')
    patch=worker.anchored_code(unit,{},'repair','test-operation')
    assert patch.files['Code.cs'].decode()=='class C { int M() { return 2; } }'
    assert seen[0]['instructions'].index('Historical hint')<seen[0]['instructions'].index('Use the host anchored repair transport')
    assert seen[0]['required_new_files']==[]
