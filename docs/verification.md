# Verification

How the pipeline establishes truth, and how a failure is attributed to a unit.

Governing principle: **a cheap structural gate must run before an expensive
behavioural one**, and the two must never be merged. Splitting compile from test is
not an optimisation — it is what makes attribution possible.

For the Unity adapter that means compilation happens outside the editor. For any
stack it means the last rung is the only one that runs code, so a failure there is
always behavioural and can only be caused by logic, never by a stray type error.

## The ladder

The shape below is core. Each rung's implementation comes from the adapter
(see `adapters.md`); the Unity instantiation is shown.

Gates run in order and stop at the first failure. Each rung proves something
narrower than the next, and each rung blames a specific unit rather than a file.

| # | Gate | Runs on | Cost | Proves | Blames |
|---|---|---|---|---|---|
| 1 | Ownership | graph host | ~0 | patches stay inside declared scope | the unit that wrote outside `owns`, or out of a frozen set |
| 2 | Parse + interface conformance | graph host, tree-sitter, no Unity | ~100 ms | files are valid C#, declared symbols exist with declared signatures | the unit that broke its own `interfaces` contract |
| 3 | Project compile | workstation, `dotnet build`; editor may stay closed | 5–10 s | the whole assembly type-checks | the first unit whose patch breaks types |
| 4 | EditMode tests | workstation, Unity Test Runner | 60–120 s | behaviour matches the frozen acceptance tests | the unit named in the failing acceptance test |

Two properties matter more than the individual gates:

- **The last rung is a pure behavioural runner.** By the time it runs, the code
  compiles, so its failures are always behavioural and never structural.
- **Test failures are self-attributing.** `acceptance` maps a test id to a unit via
  the adapter's `resolve_test_symbol`, so no bisection and no blame-by-file-path is
  needed. This is what resolves the attribution problem that subset search would
  otherwise require.

## Gate 2 in detail

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

Verification is behind one interface so topology is not baked into the graph.

```
VerifyTransport.verify(project_root, units) -> VerifyResult
```

| Implementation | Use |
|---|---|
| `LocalBatchmode` | Default. Runs `dotnet build` then Unity batchmode on the same machine. |
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
checkpointer covers a dropped connection mid-call; the retry re-runs the gate,
which is idempotent.

**The licence decides the topology.** Unity Personal/Plus licences are
machine-bound and require periodic revalidation, so Unity cannot usefully live on
a server you do not hold a seat for. Unity therefore stays on the workstation
permanently, and verification is a callback to it — not a build farm.

## Operational constraints

- **Library is single-writer.** Batchmode cannot run against a project while the
  editor has it open. The worker either drives the open editor (`McpShim`) or
  operates on a dedicated worktree. For a first project, the worktree is simpler.
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
