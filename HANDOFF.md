# Handoff

For an agent picking this up cold. Read this file, then `docs/README.md`. No prior  
conversation is required.

Repo root: this directory. The repository is **relocatable** — no absolute paths  
appear in code, docs, or config. After copying it to another machine, run  
`uv sync` (the virtualenv is machine-specific and is not committed).

## What this is

A **general frame for AI coding**. An Architect agent (CodeBuddy + OpenSpec) emits a  
task contract; a LangGraph pipeline executes it by fanning out coding units in  
parallel, enforcing file ownership, verifying through a gate ladder, and routing  
failures to the correct loop — implementation defects retried internally, contract  
defects sent back to the Architect.

Not a pipeline for one game. Unity/C# is the first verification adapter.

## Status

**Design frozen 2026-11-12. Zero implementation.**`src/` contains a wireframe written *before* the design was settled. It contradicts  
the specs in at least six places and must be rebuilt, not extended. The 7 tests in  
`tests/` pass but encode the superseded design — they are not a spec.

## Read in this order

| # | File                        | Why                                                            |
| - | --------------------------- | -------------------------------------------------------------- |
| 1 | `docs/README.md`            | Scope: general frame, Unity adapter, examples are illustration |
| 2 | `docs/boundary-contract.md` | The two artifacts, ownership rules, defect classification      |
| 3 | `docs/verification.md`      | The gate ladder and how blame is attributed                    |
| 4 | `docs/loop-control.md`      | Trend predicates, escalation, budget, termination              |
| 5 | `docs/adapters.md`          | Core versus adapter; what varies per stack                     |
| 6 | `docs/decisions.md`         | D-01…D-18 with rationale and rejected alternatives             |
| 7 | `docs/dev-environment.md`   | Verified toolchain facts for this machine                      |

## Non-negotiables

Violating any of these is a redesign, not a bug fix.

| #  | Rule                                                                                                                                   | Doc               |
| -- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| 1  | Two loops. `defect_class: implementation` never crosses the Architect boundary; only `contract` does                                   | boundary          |
| 2  | Tests are authored by `role: "test"` units and **frozen** before `role: "impl"` units run. A coder never writes the tests it must pass | boundary D-06     |
| 3  | `owns` is frozen within a cycle. Additions may only fill unclaimed space, inside `module_root`. Units are superseded, never removed    | boundary          |
| 4  | `contract_version` **is** the cycle. Do not add a cycle counter to state                                                               | decisions D-15    |
| 5  | No Unity, no C#, no `dotnet` inside core. Everything per-stack lives behind `StackAdapter`                                             | adapters D-18     |
| 6  | Path normalisation is supplied by the adapter. Never hardcode lowercase                                                                | adapters          |
| 7  | Generated files (`.meta`, `obj/`, `*.g.cs`) are exempt from ownership enforcement                                                      | adapters          |
| 8  | The ladder runs cheap → expensive and stops at the first failure. No bisection, no blame-by-file-path                                  | verification      |
| 9  | Judge runs a different model from the coder, at temperature 0, reads the patched files, and never sees coder `notes` or authorship     | boundary D-12     |
| 10 | Verification is a **blocking** call. Do not convert it to events, queues, or webhooks                                                  | verification      |
| 11 | Sole repo write is the managed block in `AGENTS.md`, flushed only on a passing run                                                     | loop-control D-05 |
| 12 | Nothing is committed to a mainline branch and nothing is pushed. Cycles land on `agent/<run_id>/cycle-<v>`                             | loop-control D-14 |
| 13 | Raw Unity logs never enter a prompt. Distilled, normalised errors only                                                                 | verification      |
| 14 | `defect_class` is per unit, never per dossier                                                                                          | boundary D-10     |

## What exists

| Path                                   | State                                                                                      |
| -------------------------------------- | ------------------------------------------------------------------------------------------ |
| `docs/*.md`                            | Complete, frozen, authoritative. Six documents                                             |
| `contracts/queue-reorder.example.json` | Illustrative contract matching the schema, including a `role: test` unit                   |
| `unity/Editor/UnityCoderVerifier.cs`   | Unity-side test runner entry point. Plausible but unverified — no Unity project has run it |
| `src/unity_coder/`                     | **Superseded wireframe.** Do not extend                                                    |
| `tests/test_core.py`                   | Tests the superseded wireframe. Will be replaced                                           |
| `requirements.txt`                     | Will be replaced by `pyproject.toml` per `docs/dev-environment.md`                         |

## Build order

Each phase ends at a state you can demonstrate. Phases 0–5 need **no Unity and no  
API key** — everything is driven by fakes. Do not skip ahead to phase 6.

| Phase | Deliverable                                                                                            | Done when                                                                                                                                   |
| ----- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | `pyproject.toml`, `uv python pin 3.12`, `.env.example`, package skeleton per `docs/dev-environment.md` | `uv sync` succeeds; `pytest` collects 0 tests without error; `langgraph dev --allow-blocking` starts and lists a stub graph                 |
| 1     | Contract loading, ownership validation, supersede semantics                                            | Collision rejected; empty `owns` rejected; `specs/` rejected as an owned path; case rule comes from a fake adapter, not a hardcoded lower() |
| 2     | `StackAdapter` protocol + Unity parse/conformance via tree-sitter                                      | Signature mismatch reported with file/symbol; generated files exempt; runs with no Unity installed                                          |
| 3     | Two-phase dispatch with the freeze gate                                                                | An impl patch touching a frozen test file is rejected by integrate; test units dispatch before impl units                                   |
| 4     | Ladder integration with a `FakeTransport`                                                              | A failure at each rung attributes to the expected unit; ladder stops at the first red rung                                                  |
| 5     | Trend classification, escalation, dossier emission                                                     | `STALLED` → `contract`; `REGRESSED` → revert unit files + escalate on second occurrence; attempt exhaustion → `contract` unconditionally    |
| 6     | Real Unity adapter: `dotnet build` + Test Runner; real model; judge                                    | One real unit completes end to end on a scratch project                                                                                     |
| 7     | `AGENTS.md` managed block, branch model, cost governor                                                 | A passing run writes constraints with provenance; a tripped ceiling produces `abandon` + dossier                                            |

## Environment facts (verified on this machine)

| Tool          | Version                                 |
| ------------- | --------------------------------------- |
| uv            | 0.10.10, with managed CPython 3.12.13   |
| system Python | 3.14.3 — do not use                     |
| .NET SDK      | 10.0.301                                |
| git           | 2.55.0                                  |
| Node          | 22.22.2 (unused)                        |
| Docker        | absent — not needed for `langgraph dev` |

Resolved and compatible: `langgraph 1.2.20`, `langgraph-cli 0.4.42`,  
`langchain-core 1.8.0`, `pydantic 2.14.3`, `tree-sitter 0.26.1`,  
`tree-sitter-c-sharp 0.23.5`.

## Traps

1. **`langgraph dev` refuses blocking I/O by default.** The verify node blocks for  
   90 s or more. Use `uv run langgraph dev --allow-blocking`. The blocking call is  
   correct in production — this is a dev-mode concession only.
2. **`langgraph dev` watches the project tree.** If this repo were nested inside a  
   Unity project, the watcher would see `Library/` and reload continuously. Keep it  
   separate.
3. **Unity writes explicit `<Compile Include>` entries.** A newly created `.cs` file  
   is not in the csproj, so `dotnet build` can pass without compiling it — a false  
   green at rung 3. Validate this on day one; if it is unreliable, demote rung 3.
4. **`Library/` is single-writer.** Batchmode cannot run while the editor holds the  
   project. Plan for a `git worktree` copy.
5. **Do not reuse wireframe patterns.** Specifically: `_normalise()` in  
   `src/unity_coder/contract.py` lowercases paths (wrong for case-sensitive  
   adapters), and `ProjectLock` is scoped to verification only (should be  
   run-scoped).
6. **Tests must not need the network or Unity.** If a test requires either, the  
   boundary has leaked into the code.
7. **Do not reintroduce a dossier-level `defect_class`.** It was a bug.

## Open items for the human

| Item                                                                            | Blocking                           | Owner                                    |
| ------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------- |
| Adapter selection mechanism (`--adapter` flag? contract field? project config?) | no                                 | needs a decision before a second adapter |
| `k = 3` and token ceilings (500k in / 150k out)                                 | no                                 | need one measurement of real convergence |
| csproj inclusion behaviour at rung 3                                            | yes, for trusting the compile gate | validate on a real Unity project         |
| One EditMode run duration on the target project                                 | no                                 | sets the cycle budget                    |
| Whether the Architect can ever run headless as a subprocess                     | no                                 | decides `SubprocessArchitect`            |

## How to know you are on track

After phase 1 and again after phase 4:

```bash
uv run pytest -q                      # no network, no Unity
uv run langgraph dev --allow-blocking  # graph compiles and is listed
```

If either needs a provider key or an editor, something is in the wrong layer.
