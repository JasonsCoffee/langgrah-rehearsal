"""Prompt formatting may shrink; every C# token and literal must remain."""
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/prompt_lexical_compaction.py')
    s=importlib.util.spec_from_file_location('prompt_lexical_compaction',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


@pytest.mark.parametrize('source',[
    'class A {\n    public int Value(int x) { return x + + x; }\n}',
    'class A { string s = @"  first\n    last"; string t = "\\u4e2d  x"; }',
    '#if UNITY_EDITOR\nclass A { public int X => 1; }\n#else\nclass A {}\n#endif\n',
    'class A { string s = $"x {1 + 2}  y"; int X => 1 /* comment */ + 2; }',
])
def test_token_and_literal_identity_survive_prompt_only_minification(source):
    m=module();result=m.compact_csharp(source)
    assert m.token_signature(result)==m.token_signature(source)
    assert len(result)<=len(source)+8


def test_prompt_keeps_all_files_criteria_and_provenance():
    m=module();body={'stage':'green','owns':['A.cs'],'criteria':['T'],
        'instructions':'Keep criteria','feedback':'actual findings',
        'files':{'A.cs':'class A {\n    public string S => "  exact  ";\n}',
                 'spec.md':'Exact normative words','rules.json':'{\n  "x": [1, 2]\n}'}}
    prompt='Implement contract.\n'+json.dumps(body)+'\nFINAL TASK INSTRUCTIONS:\nKeep criteria'
    result=m.compact_prompt(prompt);payload,end=json.JSONDecoder().raw_decode(result.split('\n',1)[1])
    assert payload['criteria']==['T'] and payload['feedback']=='actual findings'
    assert payload['files']['spec.md']=='Exact normative words'
    assert json.loads(payload['files']['rules.json'])=={'x':[1,2]}
    assert 'prompt-compaction-provenance.json' in payload['files']
    assert result.endswith('FINAL TASK INSTRUCTIONS:\nKeep criteria')


def test_invalid_source_is_not_silently_repaired_or_dropped():
    with pytest.raises(ValueError):module().compact_csharp('class Broken {')
