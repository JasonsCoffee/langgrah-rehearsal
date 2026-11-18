# Brainstorm

## Outcome and acceptance criteria

Capture the complete framework lifecycle discussed with the user: Codex with
OpenSpec prepares an executable contract and presentation baseline; LangGraph
executes isolated coding units using TDD; one Unity EditMode worker verifies
stable candidates; a human accepts the resulting experience before completion.

This is a cross-phase planning change, not completion of a handoff phase.
Implementation must retain the Phase 0 through Phase 7 build order, with new
acceptance milestones added explicitly. Governing documents are HANDOFF.md,
docs/boundary-contract.md, docs/verification.md, docs/loop-control.md,
docs/adapters.md, and docs/decisions.md. Conflicting extensions are proposals
until superseding decisions are adopted into docs/.

Observable success includes traceable task-to-unit execution, immutable tests
and visuals within a cycle, serialized verification of identified revisions,
recoverable execution, and human approval tied to the exact reviewed revision.
All framework acceptance tests use fakes and run offline without Unity.

## Current evidence and constraints

- OpenSpec is initialized with the superpowers schema. No durable capability
  specs or prior changes existed when this change was created.
- The Python source and tests predate the frozen design; neither is an
  implementation reference. The existing Unity verifier is unverified and does
  not provide the discovery, skip, baseline, or provenance evidence required here.
- Existing docs freeze tests but do not enforce observed Red or Refactor stages.
- The example contract assigns one acceptance test to multiple implementation
  units, contradicting the claim that a test name identifies one culprit.
- The loop-control action table and prose disagree on escalation timing.
- Existing documentation names CodeBuddy as Architect, omits human acceptance,
  reserves superseded ownership indefinitely, and has no execution status format.
- Framework development planning under openspec/ remains distinct from runtime
  target-project contracts under specs/<NNN-feature>/.
- Read-only target inspection identified a complete Unity host with an independent
  nested game repository at Assets/JJGame/monopoly (singular JJGame). Its own
  AGENTS.md confirms the game as the only writable module. The host and sibling
  repositories, Packages, ProjectSettings, and server sources are read-only.
- The target uses Tuanjie Editor 1.9.2 / Unity 2022.3.62t10, customized packages,
  HybridCLR, runtime assembly jj.Reserve04.Runtime, and Navigator/VVMP services.
  Docs~/ holds original game designs and the game's LLM wiki; .codex/reference/
  supplies framework/API knowledge. The game already has its own OpenSpec setup.
- cn.jj.unity-operator@0.0.1 is installed. Static source inspection confirms a
  local HTTP editor Bridge with project identity, queries, refresh, Console,
  menus, and game-local IUnityOpCommand discovery. Existing EditMode helpers use
  TestRunnerApi and fixed XML files; no generic request-specific test command
  was found in the inspected Bridge/game sources. A Luban MCP example is for
  table tooling, not evidence of editor-control MCP availability.
- Bounded Bridge discovery timed out during inspection. No Unity/Tuanjie process
  was found by the process-name check. Connectivity, compilation, discovery, and
  actual tests are unverified; installed code does not establish runtime health.

## Alternatives and trade-offs

- Keep the current OpenSpec schema and provide delegated apply: preferred over
  a custom schema, since changing artifacts alone does not delegate execution.
- Versioned JSON files and local process invocation: preferred over MCP/HTTP as
  the initial Architect boundary. A future transport can preserve the artifacts.
- Per-unit Git worktrees plus coordinator-owned integration and verification
  trees: preferred over concurrent edits to one project. Worktrees isolate files
  but require additional permission controls because Git metadata is shared.
- Sequential blocking EditMode verification: selected instead of parallel Unity
  instances or asynchronous job/webhook execution. Scheduling is coordinator-local.
- Prepare compilable component shells before freeze: preferred over asking coding
  units to repair serialized scene bindings or treating syntax errors as TDD Red.
- Explicit ownership migrations between versions: recommended instead of
  permanently reserving retired files or resetting runs to repartition work.
- External module worktrees plus a complete dedicated verification host: selected
  instead of putting worktrees under Assets/, where Unity would import duplicate
  game assemblies and assets. The nested game checkout alone cannot run Unity.
- Reuse the existing HTTP Bridge behind VerifyTransport for this target, adding
  a game-local test command and durable evidence; do not install an editor MCP or
  modify the shared package merely to wrap a deterministic test call.

## Decisions and assumptions

### User decisions

- The Architect is Codex with OpenSpec, outside the LangGraph boundary.
- All implementation units follow Red-Green-Refactor; independent test authors
  produce tests that freeze before implementation.
- Coding is parallel; Unity EditMode testing is sequential. Automated PlayMode
  policy is deferred.
- The Architect prepares placeholder art, scenes/prefabs, compilable component
  shells, explicit bindings, and the presentation baseline before contract freeze.
- Layout is immutable during LangGraph execution. Placeholder art supports human
  feedback and specifies the final-art delivery contract.
- Test author, implementing units, and integration evidence relationships must
  be explicit; integration failure may involve multiple units.
- Human acceptance follows automated execution. Feedback distinguishes a broken
  implementation from a requirement or presentation change.
- The user delegated test-validity policy details to agent judgment.
- The target's only delivered write scope is Assets/JJGame/monopoly/. Neither
  the Architect nor LangGraph may modify core utilities or other host content.
- Reuse Docs~/ original designs/wiki, existing game OpenSpec, framework knowledge,
  game components, and editor tools rather than constructing a parallel system.
- Keep Architect preparation, external coding worktrees, and the dedicated full
  Unity verification project separate. LangGraph is a decoupled executor that
  exchanges immutable inputs, verification requests, and structured results.
- The reviewed architecture uses the existing Unity Operator HTTP Bridge with a
  proposed game-local test command; live availability still requires validation.

### Proposed defaults, not independently confirmed decisions

- Exact external workspace locations and host provisioning commands are deployment
  inputs; the layout must keep all coding/integration worktrees out of Unity import.
- Explicit ownership migration at version boundaries; historical ownership stays
  recorded while each current path has exactly one active owner.
- Local status.json, progress.jsonl, result.json, and review.json records provide
  observability and completion evidence; they are not execution queues.
- STALLED escalates immediately; the first regression rolls back and permits a
  bounded retry; a second regression or failed-attempt exhaustion escalates.
- Expected Red is excluded from implementation repair counts. Already-passing
  behavior requires explicit coverage review rather than artificial breakage.
- Human review waits consume no model tokens; repair requests retain the same
  run budget. A source change invalidates prior approval.

The user authorized capturing an overall proposal; this does not make every
recommended default a separately approved runtime decision.

## Open questions

### Application review: adopted 2026-11-16

The implementation request adopts the reviewed design and recommended behavioral
defaults: version-boundary ownership migrations, external isolated worktrees,
durable status/result/review records, immediate STALLED escalation, one bounded
regression retry, expected-Red exclusion from repair counts, coverage-reviewed
already-satisfied cases, and revision-bound human approval. No scope-changing
question blocks the offline milestones. Host locations/credentials and live
Unity connectivity remain deployment preflight inputs, not guessed permissions.

Phase 0 uses pytest's native empty-suite exit code 5 as expected collection
evidence; it must not masquerade as a passing behavior suite. Subsequent phases
require exit code 0 from the actual suite and graph dev-server acceptance.

No blocking questions prevent a coherent proposal. Recommended defaults are
specified for review in design.md and are subject to adoption before runtime
implementation. Unity version, package set, target project path, and model
credentials are supplied per target project, not hardcoded into the framework.
Real compile inclusion and gate duration must be measured at the Unity milestone.
The target editor/package versions above are observed onboarding facts, not
hardcoded core defaults. Host dependency revisions, writable provisioning location,
Bridge endpoint discovery, and result storage locations must pass preflight before
any target execution. Capturing this plan authorizes no target writes or editor
startup, refresh, test execution, package installation, or host cloning.
Automated PlayMode, distributed execution, final-art production, and mainline
merge/push automation remain out of scope.
