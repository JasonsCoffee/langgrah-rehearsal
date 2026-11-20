"""A later cycle cannot silently discard an earlier global freeze."""
from test_frozen_budget_continuation import module
import pytest


def test_legacy_run_without_carry_manifest_remains_compatible(tmp_path):
    assert module().protected_tests(tmp_path,tmp_path,63)==()


def test_later_cycle_requires_explicit_frozen_continuation(tmp_path):
    folder=tmp_path/'frozen-continuations';folder.mkdir();(folder/'v64.json').write_text('{}')
    with pytest.raises(ValueError,match='frozen'):
        module().protected_tests(tmp_path,tmp_path,65)
