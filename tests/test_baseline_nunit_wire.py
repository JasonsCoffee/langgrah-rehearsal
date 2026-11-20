"""Actual Unity NUnit assertion state is Failed without a Failure suffix."""
import importlib.util
from pathlib import Path
import pytest


def data():
    s=importlib.util.spec_from_file_location('body_scope_fixture',Path('tests/test_baseline_body_scope.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    raw,contract=m.inputs();return m.helper(),raw,contract


def test_actual_failed_test_state_remains_an_assertion_not_a_setup_error():
    m,r,c=data();r['failure_details'][0]['state']='Failed'
    assert m.body_error_scope(r,c)=={'ERROR':['B']}


def test_unknown_nunit_labels_do_not_get_silently_reclassified():
    m,r,c=data();r['failure_details'][0]['state']='Failed:Cancelled'
    with pytest.raises(ValueError):m.body_error_scope(r,c)
