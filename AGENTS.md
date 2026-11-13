# AGENTS.md

Standing instructions for agents working in this repository.

This file governs **this repo** (the framework itself). It is unrelated to the
managed constraints block the framework writes into *target* repositories at
runtime — do not conflate them.

## What this repo is

A general framework for AI coding: an Architect agent emits a task contract, a
LangGraph pipeline executes it with parallel coding units, enforced file ownership,
and a verification ladder. Unity/C# is the first adapter, not the subject.

## Status

Design is frozen. Implementation has begun only where the handoff says so.

`src/unity_coder/` is a **superseded wireframe** written before the design was
settled. Do not extend it, do not treat it as a reference implementation, and do
not assume its patterns are correct. It will be rebuilt.

`tests/test_core.py` passes but tests the superseded design. It is not a spec.

## Read before writing code

1. `HANDOFF.md` — status, build order, traps
2. `docs/README.md` — scope and document index
3. The specific spec document for the phase you are working on

The `docs/` tree is authoritative. If code and docs disagree, the docs are right
and the code is wrong.

## Rules that cannot be inferred from the code

- **Core contains no Unity, no C#, no `dotnet`.** Per-stack behaviour lives behind
  `StackAdapter`. A Unity import under core is a defect.
- **Path case rules come from the adapter.** Never lowercase a path to compare it.
- **Tests are frozen before implementation runs.** A coder must never be able to
  edit the tests it has to pass.
- **`contract_version` is the cycle number.** Do not introduce a separate counter.
- **Verification blocks.** Do not convert it to events or webhooks.
- **Generated files are exempt from ownership enforcement** (`.meta`, `obj/`,
  `*.g.cs`).
- **`defect_class` is per unit.** A dossier-level verdict was a bug.
- **No absolute paths anywhere.** Not in code, docs, config, comments, or examples.
  The repository is copied between machines. Use repo-relative paths, `%PROGRAMFILES%`
  style environment variables, or `<placeholder>` syntax in documentation.

Full list with rationale: `HANDOFF.md` § Non-negotiables, and `docs/decisions.md`.

## Conventions

- Python 3.12, managed by `uv`. `uv sync`, `uv run pytest`.
- `pyproject.toml`, not `requirements.txt`.
- Type hints on public functions. No `Any` where a real type fits.
- Tests must run with no network access and no Unity installed. If a test needs
  either, the boundary has leaked.
- Do not add dependencies without flagging why. `tree-sitter-c-sharp` and the
  LangGraph packages are expected; anything else is a conversation.
- Keep `docs/` prose in the existing voice: decisions with rationale, rejected
  alternatives recorded.

## Verification

Before claiming a phase complete:

```bash
uv run pytest -q
uv run langgraph dev --allow-blocking    # graph must compile and be listed
```

State which phase acceptance criteria are met and which are not. Do not report a
phase as done when its acceptance criteria are partially satisfied.

## Never

- Commit to a mainline branch or push anywhere.
- Delete or restructure `docs/` without explicit instruction.
- Rewrite a spec to match the code. Change the code.
- Run destructive filesystem commands outside this repo.
- Edit `docs/decisions.md` entries that are already settled — add a superseding
  decision instead.
