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

## D-19 — Codex with OpenSpec delegates apply through versioned artifacts

Adopted 2026-11-16. Refines D-01 and D-15; supersedes the CodeBuddy identity in
the original handoff. Codex owns planning, export, contract revision, task
reconciliation, and archive. LangGraph owns execution. Runtime contracts remain
under specs/<NNN-feature>/; OpenSpec is not a second runtime contract store.
format_version identifies wire compatibility; contract_version remains the cycle.
The contract includes explicit task/test relationships and hashed source/profile
references. Status/result records provide observability, not execution commands.

**Why:** the boundary needs reviewable inputs and unambiguous completion evidence.
**Rejected:** replacing delegation with a custom schema alone, or hidden chat state.

## D-20 — Ownership may migrate only at a contract-version boundary

Supersedes D-04's permanent reservation of superseded files; preserves D-02.
Retain all historical unit records. Explicit migrations name source, destination,
paths, and rationale; current writable paths have exactly one active owner.
Surviving claims cannot change silently. Additions need justification, stay within
declared role scope, and retain growth/run limits. Frozen test roles and target
write policy cannot be bypassed by migration.

**Why:** permanent historical claims make retired code unmaintainable.
**Rejected:** removing history, dynamic repartitioning, or budget-resetting new runs.

## D-21 — TDD is evidenced Red, Green, and verified Refactor

Extends D-06. Independently authored tests receive scenario/validity review and
observed baseline results, then all phase-A files/configuration freeze before
implementation dispatch. Prepared compilable shells allow behavioral Red.
Invalid setup, syntax failures, zero tests, unexpected skips, and missing tooling
are not Red or Green. Already-passing behavior needs independent coverage review.
Refactor preserves ownership/bindings and needs passing evidence or a recorded
no-change decision. Defective frozen tests return for Architect revision.

**Why:** immutable tests alone prove neither useful coverage nor actual TDD.
**Rejected:** implementers editing their tests or deliberately breaking satisfied code.

## D-22 — Shared failures preserve multiple related units

Supersedes D-07's unique attribution by acceptance name; preserves the ladder.
Declare test author and implementing unit IDs separately. Evidence identifies the
snapshot, contributing patches, and involved unit set; classification remains per
unit under D-10/D-12. Coordinate bounded repairs within existing ownership or
escalate ambiguous scope/interface defects. Never bisect or blame by file/test name.

**Why:** one behavioral test can legitimately span several implementation units.
**Rejected:** inventing a unique culprit or allowing coordinated repair to expand scope.

## D-23 — Retry policy is deterministic across TDD stages

Supersedes D-11's ambiguous regression timing and the conflicting original action
table. Expected baseline Red consumes tokens but not implementation repair attempts.
STALLED escalates immediately. First regression restores safe owned state and
permits one retry within k; second regression or failed-attempt exhaustion escalates
regardless of judge output. A successful final permitted attempt passes. Compare
normalized equivalent evidence; stage transitions and human repair do not reset
the cycle's repair allowance or run-level budgets. Keep new-cycle windows bounded
by retained resource accounting.

**Why:** cosmetic change and stage changes cannot create artificial convergence.
**Rejected:** unlimited implementation verdicts and resetting counters on refactor.

## D-24 — Presentation is an Architect-prepared immutable baseline

Extends D-02/D-06/D-18. The Architect reuses or prepares feature assets, scenes,
prefabs, required component shells, and explicit bindings before freeze. Art is
placeholder delivery material plus an artist contract. Preserve layout, importer
settings, serialized interfaces, and identities; generated-file ownership
exemptions do not bypass integrity or target scope. Runtime mutations are declared.
Final-art replacement is a separate validated and human-reviewed change.

**Why:** coders need real interfaces and humans need a coherent experience to review.
**Rejected:** coding agents inventing or repairing frozen layouts, final-art polish
as a prerequisite, and hardcoding Unity presentation concerns into core.

## D-25 — External module worktrees feed one dedicated complete verifier

Refines D-08/D-13/D-14/D-17. Isolate coding and integration outside Unity-imported
directories. The game repository is separate from the complete host. Only the
coordinator integrates; only the worker materializes an identified candidate at
the authorized game mount in a dedicated full host with fixed dependencies.
Keep the user's starting tree untouched and retain candidates on abort. Worktrees
need host-enforced filesystem/command restrictions; shared Git metadata is protected.
Record operation intent before filesystem effects and reconcile after crashes.

**Why:** checkpoints and worktree separation alone do not make effects transactional.
**Rejected:** duplicates under Assets/, shared live edits, and blind patch replay.

## D-26 — Accepted pass requires revision-specific human approval

Refines D-05/D-14. All-green automatic execution yields awaiting_human_review.
Review the exact contract/baseline/candidate and required interactions. Implementation
findings stay within execution where feasible; requirement/layout findings return
for revision. Repaired content needs new evidence and approval. Flush confirmed
constraints only after approval, preserving provenance and the 40-entry archive
policy. A metadata-only completion commit records its approved parent and cannot
alter reviewed execution content. Never merge/push automatically.

**Why:** EditMode results cannot prove visual fidelity or complete experience.
**Rejected:** treating automated green as final acceptance or every human finding
as a contract defect.

## D-27 — Target policy and existing editor capabilities are execution inputs

Refines D-08/D-18 for the first target. Export hashed applicable rules and source
provenance from the game knowledge/wiki/OpenSpec; core remains stack-agnostic.
The allowed target game mount is independent of contract ownership and cannot
expand. For monopoly it is Assets/JJGame/monopoly/; shared source/settings remain
read-only. Reuse Unity Operator HTTP behind a blocking VerifyTransport, adding
only a game-local test command. Bridge task/menu success is not test completion;
durable request identity, callback results, bounded reload recovery, and exact
project identity are mandatory. Missing tooling is operational, never unit blame.

**Why:** the target already supplies editor control and has strict hot-update rules.
**Rejected:** new MCP infrastructure without need, modifying shared packages, and
allowing coding units arbitrary editor commands. Live operation remains unverified
until the dedicated target milestone.

## D-28 — Explicit provider-controlled judge temperature

Supersedes only the mandatory temperature-zero clause of D-12. The user approved
provider-controlled temperature for the configured reasoning judge after the
strict request failed and its catalog entry omitted temperature support.
Temperature zero remains the default; an explicit `temperature_mode = "provider"`
omits that parameter instead of guessing a supported value. Preserve configured
reasoning effort and record the policy in durable paid-call identity. Never switch
temperature policy or models automatically after a provider error.

Judge independence, full patched-file evidence, exclusion of coder notes and
authorship, and deterministic retry/escalation backstops remain mandatory.
Provider-controlled temperature is not a claim of deterministic output.

**Why:** the selected judge can be used without requesting an unsupported control.
**Rejected:** silent parameter dropping, automatic model substitution, and treating
temperature zero as a guarantee of reproducibility.

## D-29 — Authenticated recovery after cycle-budget abandonment

Supersedes only the terminal treatment of cycle-budget abandonment in D-25.
An explicit trusted human authorization may extend a stopped run's cycle ceiling
and advance to the consecutive validated contract. It does not raise input or
output token ceilings, reset accounting, reopen accepted/cancelled runs, or
authorize human acceptance. The host authenticates an authorization bound to the
run, previous contract and exact abandonment result digest, with actor, provenance
and a bounded new cycle ceiling. Workers and the retained Git candidate must be
reconciled under the held run lease before recovery.

Archive original invocation, result, budget, executor, dossier and progress bytes.
Persist recovery intent before changes, retain all calls and uncertain reservations,
and publish the amended ledger last. Reconnect accepts only original or intended
bytes; conflicting evidence stops. Preserve global progress order and all prior
cycle/unit lineage. Token exhaustion requires a separate policy and cannot use
this cycle-only recovery. Ordinary rework and operational resume retain their
existing conditions; recovery never converts abandonment into rework or pass.

**Why:** the user authorized safe same-run continuation after the lobby rehearsal
exhausted cycles while token allowance remained. The previous runtime had no
supported transition for that condition.
**Rejected:** clearing the stop flag manually, rewriting the abandoned outcome,
resetting budgets, replaying old operation IDs or silently adding unbounded cycles.

## D-30 — Explicit token-bound recovery grants

Extends D-29's separate-policy requirement for token exhaustion. A
TokenRecoveryGrant binds explicitly authorized total input/output ceilings to the
same actor, provenance, run, previous contract and exact abandonment-result hash.
It may recover a token-reservation stop before the cycle ceiling is exhausted.
Every ceiling must be nondecreasing, at least one authorized bound must grow,
and the new token allowances must exceed actual plus uncertain usage. Unit growth
limits, all call records, lineages, history and terminal evidence remain unchanged.
The original RecoveryGrant remains cycle-only and its audit representation stays
compatible with earlier records. Publication and interruption checks remain D-29's
leased, archive-first, ledger-last transition into the consecutive contract.

**Why:** the user approved total token ceilings of 6,000,000 input / 1,800,000
output after the same run hit its input-reservation limit under twelve cycles.
**Rejected:** modifying an active worker's ledger in place, refunding prior calls,
silently increasing ceilings, or treating a token amendment as human acceptance.

## D-31 — Structured output and context failures require explicit reconciliation

Refines D-12, D-21 and D-25. Invalid model output is an operational boundary
failure, not a source-validity verdict or unit attempt. Keep the paid receipt and
usage; never replay it automatically. Negative well-formed source reviews retain
the actual explanation and remain subject to bounded preparation.

Preparation feedback is per author and persists with its checkpoint, separately
from implementation feedback. Trusted hosts can declare exact required context
hashes; all five model stages validate them before dispatch and expose a manifest
of the actual supplied text. Missing context is not blamed on the coder.

Owner reconciliation of a pending effect requires its unchanged identity, a
trusted validating callback and existing hashed evidence. Preserve original intent
identity and proof in the completed receipt. Normal ownership, frozen tests,
accounting and independent review still apply; no model can select this callback.
See runtime-resilience.md for the public boundary, limits and deferred proposals.

**Why:** rehearsal exposed malformed JSON escaping normal recovery, feedback
leaking between authors, omitted prompt guidance and bespoke interrupted-effect
recovery. These defects are reusable runtime concerns.
**Rejected:** silent JSON repair, replaying uncertain requests, trusting a coder's
claim of success, inferring missing context, or reusing review from owned bytes alone.
