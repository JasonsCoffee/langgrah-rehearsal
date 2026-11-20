"""Reusing frozen source is not an independent review approval."""
from test_doubled_lobby_budget import module
import pytest


def test_only_exact_frozen_author_bytes_can_be_reused():
    assert module().reusable_source(('Tests/A.cs',),{'Tests/A.cs':'same'},{'Tests/A.cs':'same'})
    assert not module().reusable_source(('Runtime/A.cs',),{'Runtime/A.cs':'same'},{'Tests/A.cs':'same'})


def test_drift_fails_before_any_author_request():
    with pytest.raises(ValueError):module().reusable_source(('Tests/A.cs',),{'Tests/A.cs':'changed'},{'Tests/A.cs':'same'})
