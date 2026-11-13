"""Graph wiring and CLI.

    python -m unity_coder.graph --contract tasks.json --project-root <unity-project>

The whole loop is one checkpointed graph: contract -> partition -> fan out
coders -> integrate -> verify -> judge -> (handoff | rework | abandon).
"""

from __future__ import annotations

import argparse
import os
import sys

from langgraph.graph import END, START, StateGraph

from .architect import ManualArchitect, StaticArchitect
from .models import ChatModelClient, ScriptedClient
from .nodes import Nodes
from .state import WorkflowState


class _LazyChat:
    """Defers provider construction so importing the module never fails."""

    def __init__(self) -> None:
        self._inner: ChatModelClient | None = None

    def complete(self, system: str, user: str) -> str:
        if self._inner is None:
            self._inner = ChatModelClient()
        return self._inner.complete(system, user)


def build(model=None, architect=None, unity_exe=None, commit=False, checkpointer=None):
    from langgraph.checkpoint.memory import MemorySaver

    nodes = Nodes(
        model=model or _LazyChat(),
        architect=architect or ManualArchitect(),
        unity_exe=unity_exe,
        commit=commit,
    )

    g = StateGraph(WorkflowState)
    g.add_node("load_contract", nodes.load_contract)
    g.add_node("partition", nodes.partition)
    g.add_node("code_unit", nodes.code_unit)
    g.add_node("integrate", nodes.integrate)
    g.add_node("verify", nodes.verify)
    g.add_node("judge", nodes.judge)
    g.add_node("rework", nodes.rework)
    g.add_node("handoff", nodes.handoff)
    g.add_node("abandon", nodes.abandon)

    g.add_edge(START, "load_contract")
    g.add_edge("load_contract", "partition")

    # fan-out: one coder per unit, dispatched dynamically
    g.add_conditional_edges("partition", nodes.dispatch, ["code_unit"])

    # fan-in: integrate runs once after every dispatched coder completes
    g.add_edge("code_unit", "integrate")
    g.add_edge("integrate", "verify")
    g.add_edge("verify", "judge")

    g.add_conditional_edges(
        "judge",
        nodes.route_after_judge,
        {"handoff": "handoff", "rework": "rework", "abandon": "abandon"},
    )
    g.add_edge("rework", "partition")
    g.add_edge("handoff", END)
    g.add_edge("abandon", END)

    return g.compile(checkpointer=checkpointer or MemorySaver())


# Entry point used by `langgraph dev` via langgraph.json
graph = build()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LangGraph pipeline for Unity C# coding units")
    parser.add_argument("--contract", required=True, help="tasks.json emitted by the Architect")
    parser.add_argument("--project-root", required=True, help="Unity project root")
    parser.add_argument("--max-cycles", type=int, default=3)
    parser.add_argument("--thread-id", default="unity-coder")
    parser.add_argument("--mock", action="store_true", help="scripted model, no provider calls")
    parser.add_argument("--serial", action="store_true", help="force max_concurrency=1")
    parser.add_argument("--commit", action="store_true", help="git commit each cycle")
    parser.add_argument("--static-architect", action="store_true", help="replay units unchanged")
    parser.add_argument("--architect-timeout", type=int, default=1800)
    args = parser.parse_args(argv)

    model = ScriptedClient() if args.mock else None
    architect = (
        StaticArchitect() if args.static_architect else ManualArchitect(timeout_s=args.architect_timeout)
    )

    app = build(model=model, architect=architect, unity_exe=os.environ.get("UNITY_EXE"), commit=args.commit)

    config = {
        "configurable": {"thread_id": args.thread_id},
        "recursion_limit": 200,
        "max_concurrency": 1 if args.serial else 8,
    }

    final = app.invoke(
        {
            "contract_path": args.contract,
            "project_root": args.project_root,
            "max_cycles": args.max_cycles,
            "phase": "start",
        },
        config=config,
    )

    print("\n=== run log ===")
    for line in final.get("log", []):
        print(" ", line)

    phase = final.get("phase", "unknown")
    print(f"\nphase: {phase}")
    if final.get("dossier"):
        print(f"dossier: {final['dossier'].get('summary', '')}")
    return 0 if phase == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
