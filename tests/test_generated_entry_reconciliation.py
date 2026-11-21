"""Known generated lifecycle drift never authorizes unrelated source adoption."""
import importlib.util
from pathlib import Path
import pytest


def module():
    p=Path('openspec/changes/rehearse-monopoly-game-lobby/generated_entry_reconciliation.py')
    s=importlib.util.spec_from_file_location('generated_entry_reconciliation',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fixture():
    before=b'class Monopoly {\n    public void OnDestroy()\n    {\n        Guard();\n    }\n}'
    insert=b'\r\r\n#region GeneratedBreak\r\r\n        Context.Break();\r\r\n#endregion\r\r\n'
    after=before.replace(b'        Guard();',insert+b'        Guard();')
    return before,after


def test_exact_generated_insertion_is_identified_without_modifying_source():
    before,after=fixture();assert module().generated_insertion(before,after).replace(b'\r',b'').strip()==b'#region GeneratedBreak\n        Context.Break();\n#endregion'


@pytest.mark.parametrize('bad',['other_call','deleted_code','different_method'])
def test_other_runtime_changes_are_not_treated_as_generated_output(bad):
    before,after=fixture()
    if bad=='other_call':after=after.replace(b'Context.Break();',b'ChangeWallet();')
    if bad=='deleted_code':after=after.replace(b'Guard();',b'')
    if bad=='different_method':before=before.replace(b'OnDestroy',b'Other');after=after.replace(b'OnDestroy',b'Other')
    with pytest.raises(ValueError):module().generated_insertion(before,after)


def test_only_one_exact_entry_drift_is_permitted_in_full_snapshot():
    m=module();expected={m.ENTRY:'old','Assets/Other.cs':'same'};actual=expected|{m.ENTRY:'generated'}
    m.validate_snapshot(expected,actual,'old','generated')
    with pytest.raises(ValueError):m.validate_snapshot(expected,actual|{'Assets/Other.cs':'changed'},'old','generated')
    with pytest.raises(ValueError):m.validate_snapshot(expected,actual|{'Assets/New.cs':'new'},'old','generated')


def test_repaired_candidate_must_keep_generated_break_inside_on_destroy():
    m=module();good=b'class Monopoly { public void OnDestroy() {\n#region GeneratedBreak\nContext.Break();\n#endregion\n Guard(); } }'
    m.validate_lifecycle(good)
    with pytest.raises(ValueError):m.validate_lifecycle(good.replace(b'OnDestroy',b'Other'))
    with pytest.raises(ValueError):m.validate_lifecycle(good.replace(b'Context.Break();',b'Guard();'))
