# Verification

How the pipeline establishes truth, and how a failure is attributed to a unit.

Governing principle: **a cheap structural gate must run before an expensive
behavioural one**, and the two must never be merged. Splitting compile from test is
not an optimisation — it is what makes attribution possible.

For the Unity adapter, the compile gate must establish actual source inclusion
before test execution. Tests then report behavioral evidence separately from
runner/setup/operational failures; reaching the test rung alone does not prove
that a failure is behavioral.

## The ladder

The shape below is core. Each rung's implementation comes from the adapter
(see `adapters.md`); the Unity instantiation is shown.

Gates run in order and stop at the first failure. Each rung proves something
narrower than the next. Evidence retains the related unit set; the independent
judge routes ambiguous/shared failures instead of inventing a unique culprit.

| # | Gate | Runs on | Cost | Proves | Blames |
|---|---|---|---|---|---|
| 1 | Ownership | graph host | ~0 | patches stay inside declared scope | the unit that wrote outside `owns`, or out of a frozen set |
| 2 | Parse + interface conformance | graph host, tree-sitter, no Unity | ~100 ms | files are valid C#, declared symbols exist with declared signatures | the unit that broke its own `interfaces` contract |
| 3 | Project compile | dedicated worker, validated compile backend | measured per target | the whole assembly type-checks | related candidate units; evidence-based routing |
| 4 | EditMode tests | dedicated worker, Unity Test Runner | measured per target | behavior matches executed frozen tests | declared test/implementation relationships and candidate evidence |

Two properties matter more than the individual gates:

- **The last rung follows successful compilation.** Runner failures, missing tests,
  and stale evidence remain distinct from assertion failures.
- **Test failures preserve declared relationships.** test_links distinguish
  authors and implementing units; a shared failure can implicate several units.
  Snapshot/patch evidence and the independent judge route bounded owned repairs,
  or ambiguous scope escalates as contract. Never bisect or blame by test/file
  name alone (D-22 supersedes the original unique-attribution assumption).

## Gate 2 in detail

The offline TDD coordinator records reviewed test authors and baseline evidence
for every active implementation unit before freezing the global test/config set.
It rejects missing/zero/skipped/inconclusive execution and nonassertion failures
as Red. An already-passing baseline requires a recorded coverage review. Hashes
bind baseline test bytes to the freeze and are rechecked before dispatch and
stage transitions, together with referenced specification/profile artifacts.

Green retains owned file contents and a snapshot identity. Failed Refactor
restores those owned contents, retains the repair count, and leaves peer work
untouched. No-change Refactor requires verified Green plus a reason. Shared
verification can remain pending without spending an implementation attempt.
TDD stages are separate from the later retry trend classifier. Preparation has
its own bound; usage records are idempotent per call and include test work.
Durable transaction recovery and paid-call reservations arrive at their later
milestones; in-memory coordination alone does not claim crash safety.

Parse each patched `.cs` with a C# grammar (tree-sitter is sufficient; no Roslyn,
no DLLs, no Unity). Check:

1. The file parses.
2. Every symbol declared in the unit's `interfaces` is present.
3. Declared signatures match exactly (`ReorderQueue(int from, int to)`).

This is the cheapest gate that can catch cross-unit breakage, and it catches the
most common one: a unit silently changing the interface another unit was told to
depend on. It runs in the same process as the graph, so it costs nothing to keep
on permanently.

## Gate 3 in detail

`dotnet build` against Unity's generated solution. Unity writes `.csproj` files
with explicit `<Compile Include>` entries, and `Library/ScriptAssemblies`
persists with the editor closed — so this works without opening Unity.

**Known caveat, validate on day one.** Because includes are explicit, a *newly
created* `.cs` file is not in the csproj and will not be compiled: a false green.
Two mitigations:

- have the worker inject new files into the csproj before building, or
- maintain a glob-based shadow csproj used only for the compile gate.

If neither proves reliable, demote rung 3 and accept 90-second compiles at rung 4.
A false green here is worse than a slow gate, because it moves a structural
failure into the test rung where the evidence is misleading.

## VerifyTransport

File-protocol readers may retry transient Windows PermissionError for at most two
seconds while an atomic snapshot is replaced. Successful reads must parse complete
JSON; malformed JSON, unrelated I/O errors, and persistent denial remain failures.
This clarification was explicitly approved with progress-test revision 2.

The implemented local ladder accepts a VerificationRequest identifying run,
contract version/hash, candidate, presentation, coding/host profiles, selection,
and full-suite intent. Compile/test evidence must echo that entire immutable
request. One ladder serializes calls to its worker and blocks to completion;
cross-process host leases and materialization remain separate deployment layers.
An incomplete selection, absent/zero/skipped/inconclusive execution, or conflicting
outcomes cannot pass. A focused pass never sets full_suite_verified.

SharedFailure records failing tests, author units, implementing units, candidate,
and contributing patch identities. RepairRouting retains per-unit classifications.
A missing/ambiguous judgment or repair outside owned/frozen bounds prevents
coordinated dispatch and escalates that unit. Invalidation follows dependencies
and shared-test relationships while retaining unrelated evidence. Failed repair
round IDs charge each participant only once; persistence belongs to the journal.

Verification is behind one interface so topology is not baked into the graph.

```
VerifyTransport.verify(project_root, units) -> VerifyResult
```

| Implementation | Use |
|---|---|
| `UnityOperator` | First target: existing HTTP Bridge, game-local callback-based test command, dedicated complete host. |
| `LocalBatchmode` | Alternative backend requiring separate validation; not the first target's default (D-27). |
| `HttpWorker` | Graph on another host; POSTs to a worker co-located with the editor. |
| `McpShim` | Only if the editor must stay open and interactive. Wraps MCP or the Editor API behind the same interface. |

**Why not MCP as the primary transport.** MCP exists to expose tools to a model.
Routing a deterministic compiler call through a protocol designed for
nondeterministic tool selection adds an indirection with no benefit, and UnityMCP
requires an interactive editor. Batchmode returns structured results and is
reproducible. If MCP is wanted for other reasons, it belongs behind
`McpShim`, not in the graph.

## Topology

```
graph host                              architect workstation
  LangGraph runtime                       verify worker
  VerifyTransport  ──── POST /verify ───▶  dotnet build
                   ◀─── results ─────────  Unity Test Runner
```

The call **blocks**. From the graph's perspective verification is a slow function
call, so the loop stays closed and no event plumbing is needed. LangGraph's
checkpointer records graph state, while the operation journal reconciles a dropped
connection with durable request evidence and live worker ownership before retry.
Never assume a lost response means the test command did not execute.

**The licence decides the topology.** Unity Personal/Plus licences are
machine-bound and require periodic revalidation, so Unity cannot usefully live on
a server you do not hold a seat for. Unity therefore stays on the workstation
permanently, and verification is a callback to it — not a build farm.

## Operational constraints

- **Library is single-writer.** Batchmode cannot run against a project while the
  editor has it open. The first target worker drives the existing HTTP Bridge in
  its dedicated complete host; external module worktrees contain coding state.
- **Run-scoped lock.** `<project>/.agent/run.lock` holds the run id, not just the
  verify window. Two runs must not interleave writes to the same tree; locking
  only during verification leaves the integration window unprotected.
- **Per-unit snapshots.** Because units own disjoint files, the graph snapshots
  each unit's owned files before applying its patch. A regressing patch is
  reverted per unit, not per cycle.

## VerifyResult

```json
{
  "gate": "tests",
  "compiled": true,
  "compile_errors": [],
  "tests_total": 84,
  "tests_failed": 1,
  "failing_tests": ["QueueReorderTests.Reorder_PreservesCustomerIdentity"],
  "duration_s": 71.4
}
```

`compile_errors` entries are normalised for the coder, not raw log lines:

```
QueueSystem.cs:42 [CS0246] The type or namespace name 'Tray' could not be found
```

Raw Unity logs (thousands of import and asset lines) never reach a model. They
are written to disk and referenced by path only.

## Failure semantics

## TDD, frozen inputs, and observed evidence (D-21 through D-27)

Phase A authors tests independently, checks scenario coverage/setup/discovery,
and observes expected behavioral Red on the prepared compilable baseline. Freeze
all tests and test-selection/configuration before phase B. Invalid setup, syntax
failure, missing tooling, zero discovered/executed tests, unexpected skips, or
inconclusive outcomes are never accepted Red/Green. Existing satisfied behavior
needs independent coverage review. Defective frozen tests require a new contract.

Every implementation unit reaches verified Green before Refactor; retain the
Green snapshot and rerun after cleanup or record a no-change decision. Refactor
cannot alter ownership, tests, serialized interfaces, or frozen layout. Shared
tests can wait for a declared candidate group without blaming missing peers.
Focused tests support feedback; only the final full required integrated suite
permits human review. Record requested/discovered/executed IDs and all counts.

The coordinator alone integrates external coding worktrees. The worker alone
materializes exactly one game candidate in a complete fixed host. Reject stale
dependency bases, preserve tracked metadata, remove only stale managed candidate
files, and protect shared modules/settings. Reconcile import-generated identities
before final snapshot acceptance; then lock source/assets for the entire ladder.
Other units can keep coding. Results identify request/run/contract/hash, candidate,
baseline/coding/host profile hashes, selections, diagnostics, and duration.

For the first target, Bridge discovery validates exact project identity, refresh
is followed by compile/reload readiness and fresh Console evidence, and a game-local
test command reports callback completion durably. Menu/Bridge task success is not
test pass. Reload can erase memory task IDs; reconcile durable request identity
before a bounded retry. The LangGraph-facing VerifyTransport call still blocks.

Automated success yields awaiting_human_review. Review the runnable exact candidate
against design references and interactions, excluding final-art polish. Human
implementation findings repair within the current contract/budget; layout changes
return for Architect revision. Only explicit approval of unchanged content can
produce accepted pass. See loop-control.md for recovery and final constraint flush.

### Failure routing

- A gate failure stops the ladder. Later gates are not run — evidence from a
  deeper gate is meaningless when a shallower one is red.
- The failing gate is recorded in the dossier, so the Architect knows how deep
  the failure went.
- A gate that cannot run (missing Unity, locked project, worker unreachable) is
  an **operational** failure, not a unit failure. It aborts the run without
  consuming a cycle or a unit attempt, and never produces a dossier.

## Open items

- Validate the csproj concern for rung 3 before relying on it.
- Measure one full ladder on the target project; the numbers above are estimates
  and set the cost ceilings in `loop-control.md`.

## Production scheduling and callback evidence

The production coordinator admits completed candidates sequentially while other
coding workers remain active. Focused early verification blocks the coordinator
and is provisional; final integrated verification still gates human review.
Shared acceptance waits for all implementers, including serial dependencies with
no frozen interface. Unfinished unrelated units do not cause premature full-suite
failures during a completed group's Refactor verification.

The Unity callback preserves failure state/site/messages and suite-only failures.
Some Unity runner versions lose the failure site for setup assertions but retain
a setup/teardown message prefix. Such prefixed failures are conservatively treated
as nonbehavioral; they cannot establish Red or pass even if all leaves pass.
The isolated callback rehearsal covers these cases without selecting game tests.
