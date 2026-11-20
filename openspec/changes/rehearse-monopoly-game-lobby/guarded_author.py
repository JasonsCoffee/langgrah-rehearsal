"""Bounded delegated repair follow-up; no handwritten test implementation."""
from collections.abc import Callable,Mapping
from unity_coder.core.local_executor import WorkerPatch


def authored_repair(generate: Callable[[str,str],WorkerPatch], feedback: str, operation: str,
                    original_sources: Mapping[str,bytes], must_change: bool) -> WorkerPatch:
    clarification=('\nTEST AUTHORING: this unit\'s owned C# tests are not frozen yet. '
        'Implement the actual requested test-body repairs, not only a provenance note. '
        'Preserve other units and every genuinely frozen input. Do not implement game business code.')
    first=generate(feedback+clarification,operation)
    changed=any(path in first.files and first.files[path]!=source for path,source in original_sources.items())
    if not must_change or changed:return first
    second=generate(feedback+clarification+'\nThe prior delegated patch changed no required C# source. '
        'Return the complete repaired C# file as well as an accurate acceptance map. '
        'Do not claim implementation in a note while omitting the source changes.',operation+'-required-csharp')
    return WorkerPatch(dict(first.files)|dict(second.files),first.reason+'; bounded delegated C# follow-up: '+second.reason)
