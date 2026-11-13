# langgraph-coding-framework

> **Status: design phase.** The frozen design lives in [`docs/`](docs/README.md).
> Nothing in `src/` implements it yet.
>
> **Taking over or starting cold?** Read [`HANDOFF.md`](HANDOFF.md) first.
> Agent instructions: [`AGENTS.md`](AGENTS.md).

A **general frame for AI coding**: a LangGraph pipeline that turns an Architect's
task contract into verified code, in parallel, with a bounded rework loop back to
the Architect.

The Architect (CodeBuddy + OpenSpec) plans. The graph executes: fan out units,
enforce file ownership, verify through a gate ladder, and route failures to the
right loop — implementation defects retried inside, contract defects sent back.

The core is stack-agnostic. Unity/C# is the first adapter; a second stack should be
an adapter, not a fork.

## Design

| Doc | Answers |
|---|---|
| [`docs/boundary-contract.md`](docs/boundary-contract.md) | What crosses the line, and who decides what |
| [`docs/verification.md`](docs/verification.md) | How truth is established, how blame is attributed |
| [`docs/loop-control.md`](docs/loop-control.md) | When to retry, escalate, or stop; what a run may cost |
| [`docs/adapters.md`](docs/adapters.md) | What varies per stack; core versus adapter |
| [`docs/decisions.md`](docs/decisions.md) | Decision log, rejected alternatives, open items |
| [`docs/dev-environment.md`](docs/dev-environment.md) | Workstation setup checklist |

## Repository layout

```
docs/           frozen design — read this first
contracts/      example task contract (illustrative paths)
src/            scaffold, predates the design; will be rebuilt
unity/Editor/   Unity-side test runner entry point
```

## Not built yet

- Two-phase cycle with the test freeze gate
- The verification ladder (ownership to conformance to compile to tests)
- Trend classification and the escalation backstop
- Run-scoped locking, per-cycle branches, cost ceilings

Each is specified in `docs/` and needs no further design decisions.
