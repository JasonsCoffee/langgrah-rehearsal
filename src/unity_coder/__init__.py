"""LangGraph orchestration for Unity C# coding units.

Kept import-light on purpose: ``unity_coder.contract`` and ``unity_coder.unity``
have no LangGraph dependency, so they stay unit-testable on their own.
"""

__all__ = ["build", "graph"]


def __getattr__(name: str):
    if name in __all__:
        from . import graph as _graph

        return getattr(_graph, name)
    raise AttributeError(name)
