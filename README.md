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

## OpenSpec workflow

The [official OpenSpec](https://github.com/Fission-AI/OpenSpec) 2.0.0 CLI is a
development-only dependency. It requires Node.js 22.12 or newer. Install it with
`pnpm install --frozen-lockfile`; Python dependencies remain managed by `uv`.
Run CLI commands as `pnpm exec openspec <command>`.

All twelve workflows are checked in under `.agents/skills/` for Codex and
`.codebuddy/skills/` for CodeBuddy: propose, explore, new, continue, apply,
update, fast-forward, sync, archive, bulk archive, verify, and onboard.
In Codex, invoke `$openspec-propose` or `$openspec-explore`; in CodeBuddy,
invoke `/openspec-propose` or `/openspec-explore`. Other workflows use the
exact skill names in their `SKILL.md` files. Newly installed skills are available
on the next turn.

`openspec/config.yaml` supplies repository constraints. Planning changes live in
`openspec/changes/`, with accepted planning deltas in `openspec/specs/`.
The frozen `docs/` design remains authoritative. Runtime contracts still live at
`specs/<NNN-feature>/contract.v<N>.json`; this integration does not implement any
framework phase or change the Architect/graph boundary.

New changes default to the local [Superpowers schema](openspec/schemas/superpowers/README.md):
brainstorm, proposal, specs, design, tasks, then apply with test freeze, review,
and fresh verification evidence. Validate it with
`pnpm exec openspec schema validate superpowers --json`.

To regenerate all twelve skills after installing the pinned CLI, run
`pnpm run openspec:refresh`. The refresh script isolates generator preferences
from your global OpenSpec profile. Keep repository guidance in `AGENTS.md` and
`openspec/config.yaml`, because generated skills are overwritten on refresh.

## Implementation remaining

- Two-phase cycle with the test freeze gate
- The verification ladder (ownership to conformance to compile to tests)
- Trend classification and the escalation backstop
- Run-scoped locking, per-cycle branches, cost ceilings

Each is specified in `docs/` and needs no further design decisions.
