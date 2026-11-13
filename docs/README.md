# Design specs

Frozen design for the Architect ⇄ LangGraph pipeline. These documents are the
contract; code is written against them, not the other way round.

Starting cold, or another agent taking over? Read `../HANDOFF.md` first — it gives
status, reading order, build order and the traps. This file is the index into the
specs themselves.

## Scope

This is a **general frame for AI coding**, not a pipeline for one game. The core —
contract, ownership, test freeze, defect classes, two loops, budget — is
stack-agnostic. Unity/C# is the **first adapter**, and the examples throughout
(`DinerState`, `QueueReorderTests`, `Assets/_Project/...`) are illustration from
that adapter, not assumptions in the design.

`adapters.md` holds the line. Any Unity reference inside core logic is a bug.

| Doc | Answers |
|---|---|
| [boundary-contract.md](boundary-contract.md) | What crosses the Architect/graph line, and who decides what |
| [verification.md](verification.md) | How truth is established, and how blame is attributed |
| [loop-control.md](loop-control.md) | When to retry, escalate, or stop; what a run may cost |
| [adapters.md](adapters.md) | What varies per stack; core versus adapter |
| [decisions.md](decisions.md) | Decision log with rationale and rejected alternatives |
| [dev-environment.md](dev-environment.md) | Workstation setup: interpreter pinning, toolchain, dev server, Windows tuning |

## Reading order

Start with `boundary-contract.md`. Everything else assumes its vocabulary:
**unit**, **contract**, **dossier**, **defect class**, **inner loop**, **outer loop**.

## Status

Design phase. Nothing in `src/` has been written against these specs yet — the
existing scaffold predates every decision here and will be rebuilt. Treat
`src/` and `tests/` as a wireframe for reference only.

Open items are listed at the end of each document and consolidated in
`decisions.md`.
