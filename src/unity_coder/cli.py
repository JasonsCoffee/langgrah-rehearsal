"""Local planning export and run observation; no implicit editor/model dispatch."""

import argparse
import json
from pathlib import Path
from collections.abc import Sequence

from .core.architect_boundary import ArchitectBoundary, discover_context
from .core.contracts import _object, _text, load_contract
from .core.ownership import confined_path
from .core.executor import ProductionExecutor


def invoke_local(boundary: ArchitectBoundary, executor: ProductionExecutor) -> dict[str, object]:
    """Invoke a host-composed executor; contracts cannot select executable code."""
    if (boundary.run_id != executor.run_id or boundary.contract.sha256 != executor.contract.sha256
        or boundary.state_root.resolve() != executor.root.resolve()):
        raise ValueError("Architect invocation differs from executor identity")
    report = boundary.observe()
    action = report["next_action"]
    if action in ("wait","ended"):
        return report
    if action in ("repair","finalize","rework") and executor.stage() == "ended":
        executor.resume_review()
    from .graph import graph
    graph.invoke({"run_id":executor.run_id,"contract_sha256":executor.contract.sha256},
                 config={"configurable":{"executor":executor},"recursion_limit":100})
    return boundary.observe()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("export-context", "status"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, required=True, help="Existing selected planning root")
        command.add_argument("--instructions", required=True, help="Root-relative pinned CLI apply JSON")
        command.add_argument("--sources", required=True, help="Root-relative source-id to path JSON")
        if name == "status":
            command.add_argument("--contract", required=True, help="Root-relative frozen contract")
            command.add_argument("--previous", action="append", default=[], help="Prior contracts in cycle order")
            command.add_argument("--state-root", type=Path, required=True)
            command.add_argument("--run-id", required=True)
            command.add_argument("--adapter", choices=["unity"], required=True)
            command.add_argument("--case-sensitive", action="store_true")
    args = parser.parse_args(argv)
    try:
        instructions = _object(json.loads(confined_path(args.root, args.instructions).read_bytes()))
        sources = _object(json.loads(confined_path(args.root, args.sources).read_bytes()))
        context = discover_context(args.root, instructions, sources={key: _text(value) for key, value in sources.items()})
        if args.command == "export-context":
            output = context.to_dict()
        else:
            # Adapter selection is a composition-root concern, never core policy.
            from .adapters.unity import UnityAdapter
            rules = UnityAdapter(case_sensitive=args.case_sensitive)
            contract = None
            for path in [*args.previous, args.contract]:
                contract = load_contract(confined_path(args.root, path).read_bytes(), args.root, rules, previous=contract)
            assert contract is not None
            output = ArchitectBoundary(args.root, args.state_root, args.run_id, contract, context).observe()
        print(json.dumps(output, sort_keys=True))
        return 0
    except (ValueError, OSError, UnicodeError):
        # Avoid echoing machine paths, private source contents, or arbitrary JSON.
        print(json.dumps({"format_version": 1, "outcome": "operational",
                          "reason": "Invalid or unavailable local input; check planning readiness, provenance and run identity"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
