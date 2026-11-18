"""Core must not assume every generated artifact is UTF-8 source text."""

from test_contracts import bundle
from test_verification import verification, run
from fakes import FakeAdapter


def test_generated_binary_is_left_to_adapter(verification):
    class BinaryAwareAdapter(FakeAdapter):
        def is_generated(self, path): return path.endswith(".generated")
        def parse_check(self, files):
            assert files["Runtime/Script/Queue/cache.generated"] == b"\xff\x00"
            return super().parse_check(files)
    verification[2]["U1-state"]["Runtime/Script/Queue/cache.generated"] = b"\xff\x00"
    assert run(verification, adapter=BinaryAwareAdapter()).status == "passed"
