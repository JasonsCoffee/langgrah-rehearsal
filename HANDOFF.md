# Handoff

For an agent picking this up cold. Read this file, then `docs/README.md`. No prior  
conversation is required.

Repo root: this directory. The repository is **relocatable** — no absolute paths  
appear in code, docs, or config. After copying it to another machine, run  
`uv sync` (the virtualenv is machine-specific and is not committed).

## What this is

A **general frame for AI coding**. An Architect agent (Codex + OpenSpec) emits a
task contract; a LangGraph pipeline executes it by fanning out coding units in  
parallel, enforcing file ownership, verifying through a gate ladder, and routing  
failures to the correct loop — implementation defects retried internally, contract  
defects sent back to the Architect.

Not a pipeline for one game. Unity/C# is the first verification adapter.

## Status

**Task 12.7 complete — 2026-11-18: 61/61 tracked tasks.**
Fresh offline suite: 468 passed, one existing collection warning, 144.12 seconds.
Production graph compiled/listed with all execution nodes; owned server stopped
and no listener remained. All 69 frozen and 125 reviewed file hashes match.
No runtime code, tests, Unity host files, game content or model budgets changed.

The final phase matrix and exact command outcomes are at the top of
openspec/changes/formalize-unity-feature-delivery/verification.md; machine-readable
checks are in final-verification.json. Normal OpenSpec validation passes; strict
validation reports the existing long independent-judge requirement as a warning.
This warning remains explicit rather than rewriting the frozen requirement.

All implementation checklist tasks are complete, but do not claim a live accepted
production delivery: production-graph-live1 is still awaiting human review, and
its live metadata-only constraint flush remains unverified. Human approval of
the separate lake visual rehearsal does not approve that model-driven run.
Production recovery/cancellation/migration are verified offline; no new paid/live
end-to-end rehearsal was performed after the review fixes. Existing Monopoly
failures remain deferred; its code and tests were untouched.

Next workflow step: review the final evidence, then synchronize capability deltas
and archive when requested. No sync/archive/commit/push occurred in task 12.7.
Earlier checkpoints below are historical.

**Task 12.6 signed off — 2026-11-18: 60/61.**
R1–R10 are resolved; compliance-review.md records scope and reviewed-files.json
identifies the uncommitted implementation. Production now overlaps focused
verification with independent coding, waits for shared groups, publishes live
activity/attempts/heartbeats, honors cancellation, and reconciles recorded effects
across interrupted stages. Unknown paid calls remain operational pending explicit
owner/usage reconciliation; no blind replay or budget reset occurs.

Twelve new offline regressions in five files and a frozen isolated C# diagnostic
fixture cover the follow-up. All 69 frozen hashes match; prior tests are unchanged.
Final offline suite: 468 passed, one existing warning (145.26 seconds). Graph
compiled/listed; owned server stopped and no listener remained.

Updated callback installed and compiled on the dedicated host. Six isolated demo
tests pass. Assertion, setup and suite-teardown probes return correct evidence;
Unity's lost setup assertion site is conservatively recovered from runner message
prefixes. Temporary diagnostic source was removed. Presentation bytes and all
3,595 original game files are unchanged; all 14 host repositories have clean
tracked files. No existing Monopoly test was selected or edited, no paid calls,
dependency changes, commits or pushes occurred. Live receipts are under
live-evidence/callback-validation/ in the change.

Next: task 12.7, final phase-by-phase acceptance and verification record. Do not
conflate the task 12.6 review with full final acceptance or automatically archive.

**Current checkpoint: 59/61 — task 12.5 accepted 2026-11-18.**
Incompatible square art was rejected without mutation;
compatible art preserved references and passed six isolated tests. The reviewer
requested a lake. The revised lake candidate is
`92e7ca321be8462a445cf1d7acc0e5f566509cadd41ea4ca6a04cce30381dba3`,
with explicit approval: "Approve lake revision and interactions". The operator
rechecked candidate and manifest bytes before recording lake/acceptance.json.
Evidence and the explicit initial change request are
under live-evidence/art-replacement/ (lake/ for the revised candidate). Do not
mistake the first candidate or previous v2 acceptance for lake approval. Current
host art differs from the accepted task-12.4 snapshot; original v2 remains intact.
The operator runner is examples/visual_baseline/art_replacement.py; see its
companion art-replacement.md. No coding budget or original game tests were touched.

**Previous checkpoint: 58/61 — task 12.4 accepted 2026-11-18.**
The user approved the isolated mint baseline, requested a warm-coral primary
button, then explicitly approved v2 and its interactions. Review receipts are
under live-evidence/visual-review/. Accepted candidate:
`4c66aaf33a38893a6488f678be469af8e2439950cc79cb434611616209bde834`.
V2 presentation identity:
`7150c88cae377b3622c22f1eb6e2c05f308de2f4c7dc33be7ef7e413c64b223a`.

Live component rehearsal used actual ReviewGate/RunLifecycle/BudgetLedger and
Unity compile/EditMode evidence, not a new exported-graph/model run. A controlled
ready-handler defect failed one of five checks and rejected old approval reuse;
restoring the exact implementation passed all five in version 1. The user's
presentation request routed to rework; coral v2 passed six tests and rejected v1
approval. Its review includes test sources/metadata and all baseline files.
Human acceptance was recorded only after the user's explicit v2 reply.

Offline suite: 439 passed, one existing warning (72.27 seconds); 58 frozen files
match. All 3,595 original tracked game files and all 14 host repos are clean.
No existing Monopoly tests ran. Rehearsal cycles 1 and 2 retain zero model calls
and usage; production-graph-live1 and its budget are untouched. The v1 external
snapshot is preserved; v2 is exported separately. No commit, merge or push.
Desktop capture could not access the minimized Unity window; fresh visual
acceptance came from the user, not an invented agent screenshot.
Remaining tasks: 12.5 artist replacement, 12.6 compliance/code review, 12.7 final
verification. No runtime metadata-only completion is claimed by this rehearsal.
Earlier checkpoints below are historical.

**Current checkpoint: 57/61 — isolated visual baseline prepared 2026-11-18.**
Task 10.3 is complete for the user-authorized synthetic FrameworkVisualDemo.
The dedicated editor has VisualBaseline open in Edit Mode. Three new demo-only
EditMode tests went Red (assets absent) then Green; the live compile gate passed.
Manual Play Mode inspection observed both ready/reset preview states. This is
agent inspection, not human acceptance or automated PlayMode policy.

Manifest identity: `cc3034ecfc1f83b968323bc35d586185576574ce79f34697f4626061dbc300c0`.
Thirteen protected files are byte-identical in host and external preparation
worktree on `codex/visual-baseline-v1`; the worktree is uncommitted. Its parent is
the pinned game revision. No mainline commit or push occurred. Review is pending;
do not dispatch coding or mark tasks 12.4/12.5 complete from this preparation.
See examples/visual_baseline/README.md and live-evidence/visual-baseline/.

New Architect tooling reuses the existing prefab layout inspector and preserves
the target's resource conventions. The synthetic fixture requires no PSD/map
conversion. An observed Tuanjie encoded-GUID mismatch prompted a frozen regression
and adapter support for editor-attested canonical/serialized identity mapping.
Offline suite: **439 passed**, one existing warning; **56** frozen files match.
All 3,595 existing tracked game files are unchanged; existing Monopoly tests were
neither edited nor executed. A shared font atlas changed during editor inspection;
its generated bytes were archived outside Assets and the pinned file restored.
No original game project, design, shared source, model settings or run budget changed.
Remaining: tasks 12.4–12.7 human/artist rehearsals and final compliance/verification.
Earlier checkpoints below are historical.

**Current checkpoint: 56/61 OpenSpec tasks complete — live run resumed 2026-11-18.**
`production-graph-live1` now reached **awaiting_human_review** through the exported
graph with the configured coder/judge. Five Unity tests passed at Green and again
after Refactor. Both implementation units are complete. Exact candidate:
`fb0ae7307066d1bec4152c45e0b13b3153aca8ab`. Review is pending; no human acceptance,
constraint flush or accepted task reconciliation was fabricated.

Investigation reproduced HTTP 429 from Baidu's upstream shared pool for the exact
coder prompt. Account credit was available; old failed calls lacked error bodies,
so their exact historical responses cannot be reconstructed. Explicitly pinned
the same DeepSeek model to `alibaba` in ignored ai.local.toml through new optional
upstream_provider support. Temperature zero, judge policy and no automatic fallback
remain unchanged. ModelCalls now persists sanitized status/limit/retry diagnostics,
retains partial content as failure evidence, reconciles reported usage even on
rejected responses, and never automatically replays a failed call. Upstream route
is part of immutable call identity; old unpinned records remain readable.

The old live checkpoint was explicitly migrated only after checking its durable
result, actual integration HEAD, clean worktree and ten frozen input hashes.
Original budget limits, cycle records and every existing call record are unchanged.
Known actual usage is 2,821 input / 4,845 output; uncertain reservations (including
two bounded diagnostic requests) remain 10,368 / 12,320. Conservative totals are
13,189 / 17,165, not actual provider billing. No budget reset or original-call replay.
Evidence: live-evidence/production-graph-resumed/; previous failures remain intact.

Fresh offline suite: **427 passed**, one existing warning; all **53** frozen file
hashes match. New diagnostics tests were RED then frozen before implementation.
Graph compile/list smoke passed and its owned server stopped. All 14 dedicated
host repositories are tracked-clean; frozen fixture bytes match host/candidate.
Existing game test failures remain deferred. Original project untouched. No commit,
push or dependency addition. UI baseline, real human/artist acceptance and final
compliance review remain outstanding. The older status below is historical.

**Previous checkpoint: 56/61.** Production stage wiring and
same-run contract transitions are implemented. `cli.invoke_local` connects the
Architect boundary to the exported graph; the host explicitly supplies a held
RunLease, run BudgetLedger, LocalExecutionServices, ModelCodingWorkers, adapter
verification/preflight and authenticated ReviewGate. No runtime is inferred from
contract JSON. The shell CLI still provides export-context/status; invocation is
the host-composed Python entry point, demonstrated in production_graph.py.

The graph now has real prepare/Red/code/verify/Refactor/final verification/review/
finalize/repair/rework stages, durable checkpoints and service receipts. Tests use
real external Git worktrees with offline model/verifier boundaries. They cover
parallel coding, sequential verification, frozen tests, bounded test preparation,
same-version human repair, exact-parent metadata completion, per-unit retry,
Refactor rollback, operational recovery, token/cycle abandonment and retained
branches. `transition_cycle` requires a matching completed rework/dossier, held
lease and reconciled workers; it preserves budgets, lineage and global progress
while archiving old active records. Interrupted transitions resume idempotently.

Fresh verification: **423 passed**, one existing collection warning. All **52**
frozen test hashes match. The actual graph compiled/listed under the dev server,
its graph endpoint returned the execution nodes, and the owned server stopped.
An initial relative-import file-loader failure was reproduced, frozen and fixed.
Tasks 12.2 and 12.3 are complete at the local integration boundary. Phase 6 UI
baseline preparation and tasks 12.4–12.7 real human/artist acceptance and final
review remain; do not claim the overall framework or live production acceptance.

Live run `production-graph-live1` used the configured models and isolated dedicated
host fixture. Independent test review completed (619 input / 210 output actual).
Initial pre-test Bridge discovery failed after compilation. A frozen regression
and bounded verified-project discovery retry fixed that interruption. The same
run resumed and executed five expected Red failures. Both subsequent coder calls
produced no usable persisted replies; it ended operationally before integration.
Unknown usage remains reserved (6,108 input / 8,192 output); conservative totals
are 6,727 / 8,402, not actual provider usage. No automatic paid-call replay occurred.
Evidence is in live-evidence/production-graph/. This run has no Green or human
acceptance. Earlier real-model component Green remains separate evidence.

The isolated fixture remains at the original baseline commit. All 14 host repos
are tracked-clean; original game and deferred game failures were not changed.
The old live service checkpoint predates the new candidate_revision checkpoint
field: any future resume needs explicit host reconciliation/migration against its
durable result and actual integration HEAD, plus accounting for uncertain calls.
Do not reset the run budget or bypass the candidate guard to make it resume.
No framework commit, push, model configuration or dependency change was made.

The following checkpoint and older status paragraphs are historical.

**Previous checkpoint: 54/61.** Task 12.1 had 25 frozen
offline boundary tests plus five frozen reconnect/CLI regressions. The generic
ArchitectBoundary discovers schema context, hashes explicit source provenance,
checks task locations/links, validates durable results against run/contract/review
identity, and routes start/resume/repair/finalize to a trusted blocking callback.
It does not edit planning tasks. The CLI supports export-context and status;
the maintained framework-apply skill explains the current boundary and limits.
Real pinned OpenSpec output exported successfully: five artifact groups, 61 tasks,
two source references, portable output. Fresh suite: 377 passed, one existing
warning; all 38 frozen file hashes match. Graph compile/list smoke passed with
PYTHONUTF8=1 and the owned server stopped. Initial smoke without that setting
failed on upstream GBK decoding; no dependency changes were needed.

Tasks 12.2/12.3 remain open: production graph/executor wiring and same-run
consecutive-contract transitions are unfinished. The current boundary deliberately
rejects changed invocation identity; do not bypass this by resetting run history
or budgets. Its pass receipts trust host-owned state and CandidateCompletion,
not model-written JSON. UI preparation and live human/artist acceptance remain
unverified. No target host or game files were changed at this checkpoint.

The external dedicated
Unity host is provisioned and open, packages resolved, and the game-local verifier
is installed. Bridge discovery/reload recovery are tested. The full existing game
suite executed 596 tests: 570 pass, 26 fail; the user explicitly deferred those
failures and authorized an isolated diagnostic first.

That two-unit live diagnostic is complete: five Red failures, A-only shared
failure attributed to A+B, then five Green and five Refactor-confirmation passes.
Both coding callbacks overlap in external worktrees; verification is sequential.
Frozen test/configuration/metadata hashes match in both worktrees, integration
and host. See the active change's live-evidence/isolated-demo/ and verification.md.
That first run used deterministic callbacks. A later real-model run completed
both A and B with the configured coder and independent judge: five Red failures,
five Green passes and five Refactor-confirmation passes, with frozen bytes intact.
Model usage was 2,414 input / 3,855 output tokens. See live-evidence/real-model/.
This is an isolated component rehearsal, not exported-graph or human acceptance.

Fresh offline suite: 347 passed, one existing collection warning. Newly frozen
regressions cover reload interruptions and machine Git newline conversion. The
new durable budget ledger passes ten tests for reservations, uncertain usage,
resume, overruns and revision/lineage continuity. Accepted constraint preparation
passes twelve frozen tests: approval/provenance, deduplication, 40-entry cap,
archive and preservation of human text. It prepares bytes without writing.
Task group 11 passes its component acceptance. BudgetGovernor connects persistent
dispatch stop, trusted worker reconciliation, retained cycle branches and budget
dossiers. Late usage reconciliation cannot reopen a stopped run. Accepted-only
metadata completion retains its separate human gate. Complete production executor
wiring is still outstanding in the delegated-apply integration milestone.

The user authorized restoring boot.config and granted standing clearance inside
the dedicated host folder. Restore succeeded; tracked host drift is clear. This
authorization does not select the original interactive game project. Existing
game failures remain deferred. Local AI configuration is populated and loads via
core/ai_models.py. Both model connections passed after the user approved D-28:
explicit provider-controlled judge temperature with medium reasoning effort.
Temperature zero remains the default; no automatic policy/model fallback. Durable model
calls reserve before dispatch and reconcile replies without automatic replay.

The exported graph remains a skeleton; fresh compile/list smoke passed and the
owned dev server was stopped. New-file compile inclusion is live-verified with a
temporary #error source and successful restoration of the exact candidate plus
five tests. A ParrelSync notice blocked reload; it was closed and recovery used a
fresh request, preserving timeout evidence. All tracked host/module trees are clean.
UI baseline preparation, delegated apply/production graph and final HITL acceptance
remain. Host readiness fingerprints are in live-evidence/host-readiness.json.
No framework commit or push was made. Demo-only commits exist on external fixture
and agent branches. Earlier checkpoints below are historical; this block and the
latest verification record supersede their readiness questions.
**Implementation authorized 2026-11-16; adopted design D-19 through D-27.**
Authoritative documentation has been reconciled. Phase 0 is complete: the
superseded source and seven wireframe tests have been retired. The new package
contains only a stack-independent stub graph; execution behavior is not yet built.

Phase 1 contract validation passes 52 offline cases: collisions/empty owns/spec
protection, adapter case semantics, dependency DAGs, hashed references, shared
mappings, consecutive revisions, migrations, growth/cycle bounds, retained
lineage, and junction confinement. The required graph compile/list check passed
again and the owned server was stopped. The additional 23 target-profile checks
also pass, covering bounded mounts/scopes, rule/source hashes, separate host/game
selectors, and provenance. Phases 1 and 2 are complete. The suite has 97 passing
offline tests, including 22 structural adapter cases. The Phase 2 graph startup
and listing check passed and its server was stopped. Phase 3 TDD and Phase 4
verification components now pass their offline acceptance checks: 154 tests total,
including freeze integrity, owned Green restoration, parallel fake dispatch,
stop-first blocking gates, stale-result rejection, and multi-unit repair routing.
The Phase 4 graph startup/listing check passed and the owned server was stopped.
Phase 5 retry trends/dossiers pass their component criteria: 180 offline tests
pass, the graph compiles/lists, and the owned dev server was stopped. Owned rollback
preserves peers and invalidates dependent/shared evidence. Workspace isolation,
durable recovery, and status are next (task group 8).
The exported dev graph remains a skeleton;
complete execution wiring, persistence, real workers/models, and human review are
still outstanding and no end-to-end delivery is claimed.

Workspace isolation now passes 13 tests using real disposable nested repositories:
external module worktrees, coordinator-only integration, preserved user edits,
stale dependency rejection, and mediated coding file tools. Unrestricted shell
agents are unsupported and fail preflight. Operation journals, leases, lifecycle,
and progress are implemented provisionally; 11/12 targeted checks pass, with the
Windows reader issue above preventing task 8.4 completion.

Verified 2026-11-16: `uv sync` exited 0 with CPython 3.12.11;
`uv run pytest -q` collected zero tests (expected native exit 5).
`uv run langgraph dev --allow-blocking --no-browser --no-reload` loaded the stub;
local `POST /assistants/search` returned graph_id `unity_coder`. The owned server
was stopped with Ctrl-C. No provider keys or Unity were needed. Windows commands
used `PYTHONUTF8=1` and workspace-local `UV_CACHE_DIR=.uv-cache`.

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
| 3  | Units and owns are frozen within a cycle. Across versions, explicit migrations can transfer current ownership; preserve history and scope | boundary D-20 |
| 4  | `contract_version` **is** the cycle. Do not add a cycle counter to state                                                               | decisions D-15    |
| 5  | No Unity, no C#, no `dotnet` inside core. Everything per-stack lives behind `StackAdapter`                                             | adapters D-18     |
| 6  | Path normalisation is supplied by the adapter. Never hardcode lowercase                                                                | adapters          |
| 7  | Generated files (`.meta`, `obj/`, `*.g.cs`) are exempt from ownership enforcement                                                      | adapters          |
| 8  | The ladder runs cheap → expensive and stops at the first failure. No bisection, no blame-by-file-path                                  | verification      |
| 9  | Judge uses a different model, temperature 0 by default or explicit D-28 provider control, reads patched files, and never sees coder notes/authorship | boundary D-12/D-28 |
| 10 | Verification is a **blocking** call. Do not convert it to events, queues, or webhooks                                                  | verification      |
| 11 | Owned code/tests and run artifacts are permitted; only accepted pass flushes the managed convention block in AGENTS.md | loop-control D-26 |
| 12 | Nothing is committed to a mainline branch and nothing is pushed. Cycles land on `agent/<run_id>/cycle-<v>`                             | loop-control D-14 |
| 13 | Raw Unity logs never enter a prompt. Distilled, normalised errors only                                                                 | verification      |
| 14 | `defect_class` is per unit, never per dossier                                                                                          | boundary D-10     |

## What exists

| Path                                   | State                                                                                      |
| -------------------------------------- | ------------------------------------------------------------------------------------------ |
| `docs/*.md`                            | Complete, frozen, authoritative. Six documents                                             |
| `contracts/queue-reorder.example.json` | Illustrative contract matching the schema, including a `role: test` unit                   |
| `unity/Editor/UnityCoderVerifier.cs`   | Unity-side test runner entry point. Plausible but unverified — no Unity project has run it |
| `src/unity_coder/`                     | Rebuilt Phase 0 skeleton; no execution implementation yet |
| `tests/`                              | Superseded suite retired; Phase 1 tests are next |
| `pyproject.toml`, `uv.lock`            | Python 3.12 package and resolved dependencies |

## Build order

Each phase ends at a state you can demonstrate. Phases 0–5 need **no Unity and no  
API key** — everything is driven by fakes. Do not skip ahead to phase 6.

| Phase | Deliverable                                                                                            | Done when                                                                                                                                   |
| ----- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | `pyproject.toml`, Python 3.12 pin, `.env.example`, rebuilt package skeleton | uv sync succeeds; pytest collects 0 tests (native exit 5 is expected); dev server starts and lists stub graph without provider keys |
| 1     | Contract loading, ownership validation, supersede semantics                                            | Collision rejected; empty `owns` rejected; `specs/` rejected as an owned path; case rule comes from a fake adapter, not a hardcoded lower() |
| 2     | `StackAdapter` protocol + Unity parse/conformance via tree-sitter                                      | Signature mismatch reported with file/symbol; generated files exempt; runs with no Unity installed                                          |
| 3     | Two-phase dispatch with the freeze gate                                                                | An impl patch touching a frozen test file is rejected by integrate; test units dispatch before impl units                                   |
| 4     | Ladder integration with a `FakeTransport`                                                              | A failure at each rung attributes to the expected unit; ladder stops at the first red rung                                                  |
| 5     | Trend classification, escalation, dossier emission                                                     | `STALLED` → `contract`; `REGRESSED` → revert unit files + escalate on second occurrence; attempt exhaustion → `contract` unconditionally    |
| 6     | Real Unity adapter: `dotnet build` + Test Runner; real model; judge                                    | One real unit completes end to end on a scratch project                                                                                     |
| 7     | `AGENTS.md` managed block, branch model, cost governor                                                 | A passing run writes constraints with provenance; a tripped ceiling produces `abandon` + dossier                                            |

Extensions are tracked in openspec/changes/formalize-unity-feature-delivery/tasks.md:
offline target policy, external worktree isolation, journal/status recovery,
presentation protection, and revision-specific review precede real target
integration. Phase 6 requires a dedicated complete host with one game candidate,
existing HTTP Bridge plus a game-local test command, Red/Green/Refactor, full
EditMode evidence, and human review. Phase 7 pass means human-accepted. Never
claim a phase complete while any required check is missing.

The first target's game repository mounts at Assets/JJGame/monopoly/. Everything
else in its Unity host is read-only source/configuration. Coding/integration
worktrees live outside Unity import; the verification worker alone controls the
dedicated complete host. Docs~/ original designs/wiki and .codex/reference/ are
Architect inputs; existing game OpenSpec is reused. Bridge installation is known,
but actual connectivity, compile inclusion, and tests remain unverified.

## Historical environment facts (2026-11-12)

These values belong to the earlier workstation inspection. On 2026-11-16 the
current workstation reports uv 0.5.27 and managed CPython 3.12.11. Revalidate
dependency resolution and graph startup rather than assuming this table applies.

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

Latest provisioning update: the selected external host now contains uengine and
all 13 required nested repositories on dfw-hecan-20261026, with clean tracked
contents. Exact revisions are in the active change's provisioned-host.json.
This supersedes the earlier baseline-selection question: remote branch content
was explicitly selected; source working changes were not copied. The Unity
project is <dedicated-host>/uframework. Package resolution (no tracked lock file),
helper installation, and live editor checks remain pending; task 10.9 stays open.

Latest live update (2026-11-16): dedicated editor is open; packages resolved;
game-local FrameworkVerify is installed with the packaged Editor asmdef including
jj.Json.Runtime. Live compilation and five existing match-flow EditMode tests
passed; evidence is in the active change's live-evidence/. These are readiness
probes, not frozen feature acceptance. Shared import material drift was restored
and stayed clean through refresh/testing. Next fix: BridgeTransport discovery
incorrectly requires health commands, but the live Bridge returns [] despite a
working main-thread command registry. Add/freeze a regression before fixing.
No full game suite, new-file negative compilation probe or multi-unit live run
has passed yet. Task completion count remains 43/61.

Latest checkpoint: Bridge discovery compatibility is fixed and live-verified via
BridgeTransport. Read-only FrameworkVerifyCapabilities avoids empty health command
lists; regression frozen before implementation. Offline suite: 282 passed.
Full game namespace EditMode suite: 596 executed, 570 passed, 26 failed, no skips
or inconclusive; see live-evidence/full-game-suite.json. Failure groups: LocalRescue
5, MonoLobby 18, PawnMotion 3. No tracked nested-repository drift after tests.
Multi-unit live acceptance is not run/completed: baseline failures require triage
or explicit separate diagnostic scope. Do not alter game logic or frozen tests
silently to obtain a green framework acceptance. Task count remains 43/61.
