# Compliance and code review — 2026-11-18

R1–R10 are resolved. Task 12.6 sign-off and final command outcomes are recorded
in verification.md. Offline production-path proof and dedicated-host callback
validation are separate evidence; task 12.7 remains final acceptance work.

Scope: all four capability deltas, authoritative docs, production graph/services,
contract/ownership boundaries, TDD and verification, workspace/recovery/budget
components, review/completion, model boundaries, adapter preparation/materialization,
and the four C# editor sources. Tests were inspected for coverage boundaries and
run offline. This is an in-session code review, not an independent external audit.
No agent delegation or paid model request was used. The dedicated host received
only the framework helper and temporary isolated diagnostic tests. Existing game
tests were not selected or edited. Installed runner source explained Unity's
setup assertion behavior; live probes validate the resulting callback fix.

## Findings fixed

| ID | Priority | Trigger and impact | Resolution and regression evidence |
|---|---|---|---|
| R1 | P1 | An allowed ownership path resolves through an internal directory alias into specs or peer content. Root confinement alone allowed a protected write. | ownership.validate_owned_path rejects redirected writable paths using adapter comparison; ExecutionHost repeats validation at write time. test_review_path_aliases.py: 2 Red failures, then Green. |
| R2 | P1 | LocalExecutionServices._context included owned code and spec, but omitted the referenced coding profile and applicable rules. Workers never received required target restrictions. | Context now includes the hash-checked profile and its hash-checked rule text; drift prevents dispatch. test_review_compliance.py covers profile delivery and both drift cases. |
| R3 | P2 | A nonempty restoration patch contains unchanged bytes. WorkspaceManager.integrate attempts an empty Git commit and aborts recovery. | After all ownership/base/dependency checks, identical bytes return the existing revision without a commit. Fourth regression in test_review_compliance.py. Ordinary model patches are already filtered by worktree capture; the defect was the direct integration/restoration path. |
| R4 | P1 | Unity callback reduced assertions, setup exceptions and parent/teardown failures to failed leaf names. Invalid setup could qualify as Red, and a suite-only teardown failure could be lost entirely. Assertion messages never reached the judge. | Callback emits failure state/site/messages and suite errors; transport requires classification for failed leaves. Generic evidence carries failure kind and messages; TDD rejects nonbehavioral evidence and judges receive diagnostics. Seven regressions in test_review_test_evidence.py. Updated C# compiled live; six demo tests and three frozen diagnostic probes passed expected outcomes. Unity loses setup assertion sites, so the callback conservatively recognizes runner setup/teardown message prefixes. See live-evidence/callback-validation/. |
| R5 | P1 | A known invalid test baseline was ended as operational rather than returned to bounded preparation. | Setup evidence now sends affected authors back to preparation, without implementation attempts or freeze; exhaustion produces contract rework. test_review_preparation_routing.py: 2 Red failures, then Green. Missing tooling still remains operational. |
| R6 | P1 | A shared failure implicates a prior batch, but _failed redispatches only the current batch. If one judge says contract, implementation findings for peers disappear from the dossier. | Repair includes implicated implementers plus dependent/shared participants; mixed dossiers retain each classification. test_review_shared_routing.py: 2 Red failures, then Green. |

No existing frozen test was rewritten. New tests were added to frozen-tests.json
before each associated implementation change. No dependencies were added.

## Production findings resolved in the follow-up

### R7 — P1: scheduling and shared candidate groups — resolved

The former whole-batch barrier prevented fast candidate verification while peers
coded. The coordinator now consumes completed futures, admits candidates serially
and invokes one blocking focused verifier while independent workers continue.
Early results remain provisional; batch Green and the final integrated suite
still gate review. Shared acceptance waits for every implementer. A serial
dependent can consume its pending shared peer without a premature failed attempt.
Frozen test_production_streaming.py proves both paths using events and disposable
Git worktrees (two Red failures).

### R8 — P1: in-flight progress — resolved

ProductionExecutor publishes before dispatch and maintains a bounded-lifetime
heartbeat while services block. LocalExecutionServices exposes unit activity,
attempt counts and exact active verification revision. The heartbeat joins on
stage exit. Frozen test_production_observation_cancel.py inspects the blocked
verifier and confirms heartbeats stop after return.

### R9 — P1: cancellation dispatch control — resolved

The trusted request_cancel entry point writes contract-bound intent. Services
check before dispatch, candidate admission and transitions. Active workers finish
and retain receipts before cancellation is recorded; later stages do not run.
Model errors cannot overwrite cancellation; uncertain usage remains available
for reconciliation. Frozen observation/cancellation and effect-edge tests cover
blocked coding, blocked verification and model error. Terminal/finalizing runs
reject new cancellation requests.

### R10 — P1: interrupted production effects — resolved

DurableEffects records stage checkpoints, fixed coding plans, worker/review/judge
call intents/results, apply before/expected/after identities and verification
receipts before stage publication. Recovery reopens owned worktrees, recognizes
only recorded parent/tree transitions and reuses completed effects. Regression
restoration retains its original base; metadata completion uses the validated
completion journal. Unknown paid calls are never automatically repeated: their
intents remain and execution stops operationally for owner/usage reconciliation.
Foreign commits, unexpected bytes and ambiguous uncommitted mutations remain
fail-closed; recovery never resets arbitrary dirty worktrees.

Frozen effect_recovery, terminal_recovery and effect_edges tests inject crashes
after candidate/rollback/completion commits and after verification/state save but
before stage receipts. They prove no duplicate coding, verification or review,
no lost retry state and conservative unknown-result handling. Two terminal and
two additional edge failures were frozen after Red; the unknown-result check
already passed and was frozen unchanged.

## Verification scope

Twelve new offline regressions in five files and the isolated C# probe fixture
were frozen without changing prior frozen tests. All 69 frozen hashes match.
The first live setup probe exposed Unity runner prefix loss; the callback was
fixed against that frozen probe and rerun successfully. Suite teardown cannot
hide behind passing leaves. Six accepted demo tests pass; presentation bytes and
all 3,595 original game files are unchanged. All 14 dedicated-host repositories
have clean tracked files. Diagnostic source was removed after evidence capture.

## Requirement coverage

The following maps every requirement heading in the four deltas to the reviewed
implementation/evidence. "Component" is deliberately distinct from production
acceptance. Source paths below are relative to src/unity_coder/core/ unless noted.

### Architect execution

| Requirement | Review disposition |
|---|---|
| Delegated apply preserves planning authority | architect_boundary.py, cli.py and boundary tests; only advisory eligible task IDs, no planning writes. |
| Versioned runtime boundary | contracts.py, cycles.py, executor.py; fixed hashes and consecutive versions, durable dossiers. Production recovery covered by R10. |
| Fixed units and validated ownership | contracts.py, ownership.py, execution_host.py and workspaces.py; R1 fixed. |
| Explicit task and test relationships | contracts.py and integration.py; production shared routing R6 fixed. |
| Architect-controlled ownership migration | contracts.py, cycles.py and budget.py; lineage and archived cycle state retained. |
| Two failure loops and independent judging | coding_workers.py, model_calls.py, loop_control.py; distinct models and explicit temperature policy; R4/R6 fixed. |
| Structured execution outcomes | executor.py and lifecycle.py support durable outcomes; active cancellation/recovery covered by R9/R10. |
| Onboarding establishes a non-expandable game boundary | target_profiles.py, ownership.py and adapter materialization; independent bounds, generated-path protection, R1 fixed. |
| Architect preserves source provenance and project knowledge | target_profiles.py and architect_boundary.py hash explicit sources; resolving source conflicts remains Architect responsibility. |
| Coding restrictions are versioned execution inputs | R2 fixed; profile/rules now delivered. Target-specific semantic compliance still needs Architect/judge review; syntax is not lifecycle correctness. |

### Parallel TDD

| Requirement | Review disposition |
|---|---|
| Tests independently authored/validated before freeze | tdd.py and local_executor.py; R4/R5 fixed. Unity callback live validation passed. |
| Red against known baseline | tdd.py; exact selected outcomes and already-satisfied coverage review. R4/R5 close setup false-Red path offline. |
| Green and Refactor require verification | tdd.py, local_executor.py, refactor regression tests; retained Green/no-change decisions. |
| Coding work is isolated | mediated ExecutionHost, external WorkspaceManager, R1 protection; arbitrary process agents unsupported. |
| Coordinator integrates sequentially | workspaces.py and local_executor.py; validated bases/dependencies, R3 fixed; production effect recovery R10 resolved. |
| Unity verification sequential and blocking | ladder lock, host guards and Bridge blocking transport; independent-coding overlap R7 resolved. |
| Evidence describes immutable inputs | verification.py, immutable requests and adapter CandidateHost; trusted host must retain lease across materialization and gates. |
| Execution cannot yield false pass | tdd.validate_behavior, ladder, Bridge callbacks; zero/skipped/inconclusive/stale rejected, R4 closes suite-only failure. |
| Integration evidence can implicate multiple units | integration.py component and R6 production fix; per-unit evidence retained. |
| Deterministic bounded retries | loop_control.py, preparation bounds, budget governor; frozen retry/refactor tests. |
| Worktrees outside Unity import | WorkspaceManager preflight and real disposable-Git tests. |
| Exactly one materialized game candidate | adapter CandidateHost; component tests and prior isolated live evidence. |
| Shared host integrity survives verification | CandidateHost hash/dependency checks; prior isolated host audits. No new host operation in this review. |

### Execution lifecycle

| Requirement | Review disposition |
|---|---|
| Architect observes progress | Production heartbeat/activity/attempt wiring passes (R8). |
| Recovery reconciles durable effects | OperationJournal/leases and DurableEffects production recovery (R10). |
| Budgets survive revisions/recovery | BudgetLedger, ModelCalls, cycles.py, BudgetGovernor; reservations survive unknown usage and cycle changes. |
| Operational abort and cancellation preserve work | isolated workspaces and operational resume tested; active cancellation R9 resolved. |
| Automated success waits for human acceptance | ReviewGate and production executor stop at awaiting_human_review; launch/interactions supplied by Architect baseline. |
| Human approval revision-specific | review.py, completion.py; exact request/files/parent, immutable approval receipts and prior live rehearsals. |
| Review feedback follows repair boundary | production repair/rework stage tests and task12.4 receipts; no agent self-approval. |
| Accepted completion preserves provenance | constraints.py, completion.py and real-Git completion tests; managed block only, no mainline merge/push. |
| Framework verification offline | full pytest suite uses fake transports/models and disposable repositories; Unity source syntax check is offline. |
| Verification transport independent | VerificationRequest and BridgeTransport exact request correlation. |
| Editor identity/reload verified | bounded Bridge discovery and reload tests; prior dedicated-host evidence. |
| Editor command cannot imply success | callback-required results, nested error handling, R4 diagnostics; updated callback compiled and tested live. |
| Editor control worker-scoped | ExecutionHost denies commands; model workers emit owned file text only. |

### Presentation baseline

| Requirement | Review disposition |
|---|---|
| Architect prepares usable baseline | adapter preparation and FrameworkVisualPreparation; isolated live task10.3 evidence. |
| Baseline validated/identified | Presentation, PreparedBaseline, ImportReport; hashes, bindings and GUID round-trip evidence. |
| Frozen presentation integrity | protected paths, metadata hashes and adapter interface checks; caller must supply protected paths/preflight to host composition. |
| Runtime behavior respects bindings | declared mutations/interface checks plus human review; no claim static syntax proves runtime UX. |
| Placeholder defines artist requirements | ArtistAsset manifest fields and accepted isolated delivery rehearsal. |
| Final-art replacement controlled later change | replacement policy and task12.5 rejected/accepted exact candidate receipts. |
| Adapter-specific presentation behavior | no Unity/C#/dotnet import or policy under core; Unity handling stays in adapter/editor tooling. |
| Prepared art belongs to game baseline | external snapshot/worktree export and byte-preserving distribution; original design sources untouched. |

## Verification and review identity

The review operates on uncommitted rebuilt source. reviewed-files.json records
content hashes and the Git base; the base alone is not the reviewed implementation.
No commit or push was made. Final command outcomes are recorded in verification.md.
Task 12.7 remains separate: final phase-by-phase acceptance and verification record.
