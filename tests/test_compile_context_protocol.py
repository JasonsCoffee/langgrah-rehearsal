"""Mechanical compile context and safe rejected-item diagnostics."""
import importlib.util
import json
from pathlib import Path
import pytest
from test_codex_backend import turn_events
from unity_coder.core.ai_models import ModelError


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/compile_failure_context.py')
    s=importlib.util.spec_from_file_location('compile_failure_context',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def test_compile_context_retains_exact_current_source_spec_and_rules():
    files={'Runtime/A.cs':'exact code','spec.md':'complete spec','rules.md':'complete rules',
           'Tests/A.cs':'unchanged frozen tests','readonly-retained-proposal/Runtime/A.cs':'old proposal'}
    v=module().curate('compile','failed',files,('Runtime/A.cs',))
    assert {k:v[k] for k in ('Runtime/A.cs','spec.md','rules.md')}=={k:files[k] for k in ('Runtime/A.cs','spec.md','rules.md')}
    assert 'Tests/A.cs' not in v and not any(k.startswith('readonly-retained-proposal/') for k in v)
    proof=json.loads(v['readonly-compile-context/provenance.json'])
    assert set(proof['omitted_provided_text_sha256'])=={'Tests/A.cs','readonly-retained-proposal/Runtime/A.cs'}


def test_behavioral_context_and_missing_owned_source_are_not_silently_trimmed():
    files={'Tests/A.cs':'full assertion','Runtime/A.cs':'code'}
    assert module().curate('tests','failed',files,('Runtime/A.cs',))==files
    with pytest.raises(ValueError):module().curate('compile','failed',files,('Runtime/Missing.cs',))


@pytest.mark.parametrize('kind',['contextCompaction','plan','commandExecution'])
def test_rejected_item_type_is_safely_attributed_without_allowing_it(kind):
    from unity_coder.core.codex_backend import parse_turn_events
    event={'method':'item/started','params':{'item':{'type':kind,'text':'secret payload'}}}
    with pytest.raises(ModelError) as caught:parse_turn_events([event]+turn_events())
    assert caught.value.diagnostics.get('item_type')==kind
    assert 'secret' not in json.dumps(caught.value.diagnostics)
