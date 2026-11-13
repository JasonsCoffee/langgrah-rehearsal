# Decision log

Each entry records what was decided, why, and what was rejected. Superseded
entries are marked, not deleted.

## D-01 — The contract lives in the repo

`specs/<NNN-feature>/contract.v<N>.json`, beside `spec.md`.

**Why:** the plan is part of project history. A cycle becomes a diffable file, so
cycle 3 regressions are attributable. It also removes any need to poll for an
Architect response: the next run is invoked with a new path.
**Rejected:** contract in a database or the graph's state — nothing to diff, and
resume-after-crash loses the plan.

## D-02 — Ownership is immutable within a cycle

`owns` may not be added, removed, or reassigned for a surviving unit mid-cycle.

**Why:** parallel coders partitioned by file ownership is the only safe form of
parallelism. Removing a path is as illegal as adding one, because it orphans files
already written this cycle. Freezing is bidirectional.
**Rejected:** dynamic re-partitioning — it makes cycles non-reproducible and
destroys per-unit attribution.

## D-03 — The judge classifies the defect

`defect_class` is assigned by the judge, per unit, with evidence.

**Why:** the judge has just read the evidence and the spec, so it is the cheapest
place to decide which loop handles a failure.
**Risk and mitigation:** a judge that keeps answering `implementation` traps the
coder forever. Countered by a deterministic escalation rule (D-11) that does not
depend on judge quality.

## D-04 — Units may be added on rework, never removed

Additions require `add_justification`, must be inside `module_root`, and must be
disjoint from the frozen ownership map. Retired units become `status: superseded`.

**Why:** revision is sometimes genuinely infeasible, and only the Architect can
judge that. Removal is forbidden because it orphans already-written files.
**Rejected:** binding `requested_changes` — it would override the Architect's
judgement about feasibility, which is the one thing only it can assess.

## D-05 — Confirmed constraints persist into `AGENTS.md`

One managed block, delimited by markers. Outside the markers is untouched.

**Why:** a constraint only reduces future cost if it reaches a future coder, and
`_conventions()` already loads `AGENTS.md` into every unit's context, so
propagation is free.
**Guards:** flushed only on a green run; provenance mandatory (a constraint that
cannot name its evidence is a situational observation); hashed for idempotency;
capped at 40 with archive rather than deletion.

## D-06 — Tests are authored and frozen before implementation

Two-phase cycle: `role: "test"` units run in phase A, their files freeze, then
`role: "impl"` units run in phase B.

**Why:** otherwise the coder certifies itself, and `assert.True(true)` passes the
gate. Freezing makes TDD a structural property rather than a prompt instruction,
and produces a legitimate red state, which the single-phase design cannot
distinguish from "tests were weakened".
**Cost:** one extra phase per cycle, and requires spec scenarios machine-readable
enough to brief a test author.

## D-07 — Verification is a ladder; Unity is the last rung

Ownership → parse/conformance → project compile → EditMode tests.

**Why:** compilation does not require Unity. Pushing compile out of Unity is what
makes attribution possible: structural failures stop before the test rung, so
Unity failures are always behavioural and always attributable via acceptance test
names.
**Rejected:** all-at-once compile plus bisection (`log₂N` extra 90-second runs),
and blame-by-file-path (wrong precisely when a unit breaks another's declared
interface).

## D-08 — `VerifyTransport` with a local default; MCP is not the transport

`LocalBatchmode` for v0, `HttpWorker` when the graph moves off the workstation,
`McpShim` only if the editor must stay interactive.

**Why:** MCP exists to expose tools to a model. Routing a deterministic compiler
call through a protocol designed for nondeterministic tool selection adds
indirection with no benefit, and UnityMCP requires an interactive editor.
**Rejected:** MCP as the primary transport; also rejected a queue/webhook model,
since a blocking call keeps the loop closed with no event plumbing.

## D-09 — Unity stays on the workstation

Verification is a callback to the Architect's machine, not a build farm.

**Why:** Unity licences are machine-bound and require revalidation, so Unity
cannot usefully run on a server without a seat. This is a hard constraint, not a
preference, and it decides the topology.

## D-10 — `defect_class` is per unit, not per dossier

**Why:** one cycle routinely contains an implementation defect in one unit and a
contract defect in another. A dossier-level verdict forces a binary choice that
does not exist and loses the distinction the two loops depend on.

## D-11 — Trend classification: change *and* progress, `k = 3`

`STALLED` (unchanged evidence hash) and `REGRESSED` (new failures appeared) both
escalate to `contract`. Attempt exhaustion escalates unconditionally.

**Why:** a stable hash means "not converging"; an unstable one does not mean
"converging". Without a regression detector, a coder that breaks five tests after
failing one looks like change rather than damage. Without `PROGRESSING` as a
proper-subset test, cosmetic edits read as progress.
**Status:** `k = 3` is an unvalidated default pending measurement.

## D-12 — Judge independence and non-blindness

Different model from the coder, temperature 0, reads the patched files, never sees
the coder's `notes` or any authorship signal.

**Why:** self-assessment inflates pass rates. And classifying
contract-vs-implementation from log text alone is impossible — an untestable
criterion looks identical to a failing implementation unless the judge reads both
the spec and the patch.

## D-13 — Run-scoped lock and per-unit snapshots

`.agent/run.lock` holds the run id for the whole run, not just verification. Each
unit's owned files are snapshotted before its patch is applied.

**Why:** locking only during verification leaves the integration window
unprotected, so two runs can interleave writes. Per-unit snapshots let a
regressing patch be reverted for one unit instead of discarding the cycle, which
is only possible because ownership is disjoint (D-02).

## D-14 — Branch per cycle; abandon restores the start branch

`agent/<run_id>/cycle-<v>`, never pushed. `abandon` checks out the start branch and
retains cycle branches for inspection.

**Why:** leaving a non-compiling tree after exhaustion poisons the next run, which
then fails verification for unrelated reasons. Git-native restoration is
reversible and leaves nothing half-applied.
**Rejected:** `git stash` — it can be forgotten and silently reapplied.

## D-15 — Cycle is derived from `contract_version`

No cycle counter in graph state; `cycle := contract_version`.

**Why:** a crash mid-cycle can otherwise double-increment, which desynchronises
the dossier from the contract. Deriving it enforces "one bump per cycle" by file
contents rather than by convention.

## D-16 — Cost ceilings: 500k in / 150k out / 3 cycles, +2 units per rework

**Why:** `k × units × cycles` is multiplicative and decision D-04 lets unit count
grow. Six units, three cycles, `k = 3` is 54 coder calls per run. Ceilings are
sized for a small first project at roughly $2–4 per run: cheap enough to iterate,
expensive enough that a runaway loop is visible rather than silent.
**Scope:** the formula is core, these constants are the Unity adapter's starting
point. Derive `k` from gate duration and the token ceiling from measured context
size per adapter — see `adapters.md`.

## D-17 — Run the graph on the workstation for v0

**Why:** the two-machine topology costs a worker, a lock protocol, and a
debugging surface before a single unit exists. `VerifyTransport` remains the seam
so the split can happen later without redesign.

## D-18 — The frame is stack-agnostic; Unity is the first adapter

Core holds only rules that would be identical for every stack. Anything that
differs — path comparison, generated-file exclusion, parse grammar, compile and
test commands, test-symbol resolution, lock scope, cost constants — lives behind
a `StackAdapter`.

**Why:** the design was worked out against one Unity project, but it is meant as a
general frame for AI coding. Baking Unity assumptions into core would make the
second stack a fork rather than an adapter, and the fork would drift.
**Consequence:** five latent bugs surfaced the moment the design was generalised —
hardcoded lowercase path normalisation, no exemption for generated files, Unity's
`Class.Method` test naming treated as universal, single-writer locking assumed as a
frame rule, and shared budget constants. All five are now adapter responsibilities;
see `adapters.md`.
**Rejected:** maintaining a Unity-specific pipeline and a general one in parallel.
The duplication drifts, and the general path never gets exercised.

## Consolidated open items

| Item | Blocks | Resolution |
|---|---|---|
| csproj explicit includes may yield false greens at rung 3 | trusting the compile gate | validate on day one; demote rung 3 if unreliable |
| `k = 3`, token ceilings | trusting the loop bounds | replace with measurements after the first real run |
| Ladder timings on the target project | sizing the cycle budget | measure rungs 3 and 4 |
