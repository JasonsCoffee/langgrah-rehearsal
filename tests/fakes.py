"""Deterministic local test doubles; no network, compiler, or editor."""

from dataclasses import replace

from unity_coder.core.evidence import CompileResult, TestResult as Result
from unity_coder.core.verification import WorkerEvidence


class FakeAdapter:
    def __init__(self, syntax=(), interfaces=()):
        self.syntax = syntax
        self.interfaces = interfaces
        self.calls = []

    def normalise_path(self, path): return path
    def is_generated(self, path): return path.endswith(".meta")
    def parse_check(self, files):
        self.calls.append("parse")
        return self.syntax
    def check_interfaces(self, files, interfaces):
        self.calls.append("interfaces")
        return self.interfaces


class FakeTransport:
    def __init__(self, compilation=None, result=None, stale=False):
        self.compilation = compilation or CompileResult(True)
        self.result = result
        self.stale = stale
        self.calls = []

    def compile(self, request):
        self.calls.append("compile")
        return WorkerEvidence(request, compilation=self.compilation)

    def run_tests(self, request):
        self.calls.append("tests")
        result = self.result or Result(request.test_selection, request.test_selection, request.test_selection, ())
        identity = replace(request, candidate_revision="old") if self.stale else request
        return WorkerEvidence(identity, tests=result)
