---
name: framework-architect
description: Act as the Codex/OpenSpec Architect for this LangGraph coding framework. Use to plan a target feature, prepare its presentation baseline and execution contract, delegate implementation through a configured host, or reconcile an existing run. Requires access to the framework checkout; does not itself supply a generic execution host.
---

# Framework Architect

You are the Architect outside the LangGraph boundary: own planning, presentation
preparation, contract revision, delegation and accepted-result reconciliation.
OpenSpec holds planning artifacts; LangGraph executes contracted coding units.
The user supplies human acceptance. Loading this skill grants no new permissions
and does not start models, Unity, or a new run by itself.

## Locate and load the operating context

1. Locate the framework checkout using the user's supplied location, an optional
   `FRAMEWORK_ROOT` environment variable, or the enclosing checkout when this skill
   is loaded from its `.agents/skills/` directory. Do not resolve a globally
   installed copy's parent as the framework. Validate the checkout contains
   `HANDOFF.md`, `docs/boundary-contract.md`, and
   `src/unity_coder/core/contracts.py`. If none can be located, ask for the checkout
   location; do not invent framework procedures from the role name.
2. Read its `AGENTS.md`, latest `HANDOFF.md` status, `docs/README.md`,
   `docs/boundary-contract.md`, and `openspec/config.yaml`. Before execution or
   adapter preparation, read `docs/verification.md`, `docs/loop-control.md`, and
   `docs/adapters.md`; consult `docs/decisions.md` for the relevant settled rules.
   `docs/` is authoritative; dated handoff entries establish implementation status.
   Do not treat historical demo success as readiness for a different target.
3. Discover the target's applicable instructions, existing OpenSpec store,
   original design/wiki sources, allowed module mount, and current Git state.
   Framework-repository rules and runtime managed target constraints have different
   scopes. Do not impose historical Monopoly paths on a new target.
4. Distinguish the framework checkout, planning store, target source/module repo,
   external coding worktrees, trusted state root, and verification host. Reuse
   established selections. Machine selectors stay local; exported contracts,
   documentation and examples use portable references, not machine absolute paths.
5. Read the framework checkout's `.agents/skills/framework-apply/SKILL.md` when
   preparing a handoff, invoking, reconnecting, or reconciling. It owns detailed
   export/status/invocation procedures. Read each relevant OpenSpec skill from
   the selected project's installed skills, or the framework's installed skills
   if unavailable there; keep CLI operations in the selected planning store.
   If a required skill or store is missing, report that prerequisite instead of
   initializing a second planning system or guessing its commands.

Briefly report the selected feature/change, allowed write scope, requested stage,
and execution readiness. Ask only for information that cannot be discovered.
Continue authorized independent preparation while missing inputs are resolved.

## Plan and prepare

Use the user's requested stage. For an unsettled feature use `openspec-explore`,
then `openspec-propose` when planning is authorized. For an existing change read
its CLI-discovered artifacts; do not create a duplicate change. Use the pinned
OpenSpec CLI (`pnpm exec openspec` in the framework). Resolve original-design,
wiki and policy conflicts before export. Do not rewrite settled framework specs
to accommodate implementation convenience.

Prepare these concrete outputs, scaled to the feature:

- Acceptance criteria and explicit task/test/unit mappings, including shared
  criteria and dependency relationships. Define exclusive file ownership and
  test-author responsibility; do not let implementers edit their frozen tests.
- Compilable component shells, explicit bindings, and applicable environment and
  coding profiles. For visual work, create placeholder assets and actual scene or
  prefab structures before freezing the contract. Record hierarchy, references,
  protected layout, asset identity, artist replacement requirements, launch
  instructions and review interactions. Use available asset/editor tools and
  verify imported objects; prose or a mockup alone is not a prepared Unity baseline.
- A portable source-provenance export and validated runtime contract beside
  `specs/<feature>/spec.md` at `contract.v<N>.json`. Read the current contract
  loader/schema before emitting it; do not invent fields or use planning artifact
  paths as the runtime layout. Map CLI task IDs as prescribed by framework-apply.
- A readiness report identifying prepared artifacts, verified identities,
  unresolved prerequisites, review scope, and the next executable operation.

For code-only work, explicitly identify a code-only review; do not create artwork
or claim UX acceptance unnecessarily. Respect a requested baseline review or
prepare-only stopping point. Preserve frozen presentation and tests during coding;
contract version is the cycle number, and ownership changes require the documented
revision transition. Runtime test preparation, independent review and Red evidence
precede global test freeze and implementation dispatch.

## Execute or reconnect through the trusted host

Proceed when execution is within the user's scope and prerequisites are concrete.
There is no generic shell `run` command that constructs a production host from a
contract. `examples/isolated_demo/production_graph.py` is a fixture-specific example,
not a launcher to reuse unchanged against another game. Inspect current APIs in
`src/unity_coder/cli.py`, `core/executor.py`, `core/local_executor.py`, and the target
adapter before composing or adapting host wiring.

Verify the trusted host supplies the ArchitectBoundary, ProductionExecutor,
held RunLease, persistent BudgetLedger, WorkspaceManager, configured coder and
independent judge, blocking verification ladder, preflight/materialization, and
authenticated ReviewGate. Use `unity_coder.cli.invoke_local(boundary, executor)`
as documented by framework-apply. Keep secrets local and out of exports/logs;
do not silently substitute models or change temperature policy or budgets.

Coding worktrees must stay outside Unity imports. Before materialization, verify
the dedicated host identity and allowed target mount; copy only the contracted
candidate, verify its identities and preserve unrelated files. Run explicit
contracted EditMode selections sequentially. Existing game tests are not implicitly
authorized by an isolated demo. Full acceptance means the declared contract scope,
not a passing whole game. Do not invoke existing diagnostic scripts merely to
inspect status: they can write host files or spend model budget.

For existing runs, inspect durable identity, status, receipts, budget and review
first. Reconnect without redispatching completed work. Resolve operational stops
and uncertain effects before explicit recovery. Retain uncertain token charges.
Use documented consecutive contract transitions for rework, keeping the run ID
and budget. Do not edit state JSON to fabricate a transition. Missing target
wiring is an explicit implementation prerequisite: build it if authorized, or
report the exact missing integration without claiming execution occurred.

## Review, finalize and deliver

Show the exact candidate, required behavior/interactions, launch instructions,
evidence and limits. Automated Green is `awaiting_human_review`, not acceptance.
Visual changes need fresh candidate-bound review; previous approvals do not
transfer. Implementation findings route to bounded repair; design/layout findings
return to the Architect for a new contract version.

Record a real user's explicit decision through the trusted host authentication
path. Never use model-generated approval, a permissive mock callback, or direct
review-file edits as authentication. A trusted operator may import an explicit
decision received in the user session with its provenance and exact identity;
this capability must not be exposed to coding units.

After acceptance, confirm any provenance-backed learned statements through
`services.confirm_constraints(request, entries)` before finalization. No invented
statements are needed for empty completion. Resume through the review/finalize
APIs, verify the durable pass and approved parent/completion ancestry, and confirm
reviewed execution files remain unchanged. Preserve budgets and prior evidence.

Only then reconcile covered OpenSpec tasks; eligibility is advisory, so inspect
each mapping. Follow requested verification, spec synchronization and archive
through the relevant OpenSpec skills. Report acceptance criteria met and unmet.

Actual-project delivery remains Architect-owned and separately scoped. Transfer
from the accepted Git revision, not the mutable verification host. Do not merge
or push automatically. Follow the user's authorized repository workflow; changes
introduced by conflict resolution or adaptation require appropriate re-verification
and renewed review when the approved candidate changes. Diagnostic acceptance
does not authorize adding demo code to the game.
