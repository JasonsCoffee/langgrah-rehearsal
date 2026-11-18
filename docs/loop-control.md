# Loop control

When to retry, when to escalate, and when to stop. Covers the inner loop
(LangGraph-owned, per unit), the outer loop (Architect-owned, per contract), and
the budget that bounds both.

## Attempt history

Each unit carries an ordered history. One entry per inner attempt:

```
{ attempt: 2, gate: "tests", evidence_hash: "9f21ab",
  failing: ["QueueReorderTests.Reorder_PreservesCustomerIdentity"],
  compile_errors: 0, trend: "STALLED" }
```

`evidence_hash` is a stable hash over `(gate, sorted failing test names, compile
error codes)`. Messages are deliberately excluded: they churn cosmetically
between attempts and would make every attempt look like progress.

## Trend classification

Computed against the previous attempt for the same unit:

| Trend | Predicate | Meaning |
|---|---|---|
| `RED` | no previous attempt | first failure |
| `PROGRESSING` | current failing set is a proper subset of previous | converging |
| `STALLED` | `evidence_hash` unchanged | not converging |
| `REGRESSED` | current failing set is **not** a subset of previous | new damage |

A stable hash means "not converging". An unstable hash does **not** mean
"converging" — hence the separate progress test. A regression detector is also
required, because otherwise a coder that breaks five tests after failing one
looks like change rather than damage.

## Inner loop actions

| Trend | Action |
|---|---|
| `RED` | retry, with the failing evidence in context |
| `PROGRESSING` | retry, with the failing evidence in context |
| `STALLED` | escalate immediately as `contract` |
| `REGRESSED` | restore the unit's owned files from its pre-apply snapshot, retry once with the regression diff; a second `REGRESSED` escalates as `contract` |
| failed attempt exhausts `k` | escalate as `contract` regardless of trend; a successful last permitted candidate passes |

`k = 3`. Two rules override the judge, and both exist because a model that
misclassifies as `implementation` would otherwise trap the coder on a unit that
can never converge:

1. STALLED escalates immediately. First REGRESSED restores safe owned files and
   permits one retry within budget; a second regression escalates (D-23).
2. Failed-attempt exhaustion escalates to contract unconditionally.

TDD stage and attempt trend are separate. Expected baseline Red is not an
implementation repair attempt, but all model calls consume tokens. Green,
Refactor, and human implementation repair share the cycle allowance. Test authors
have bounded preparation attempts. Already-satisfied behavior needs coverage
review, never artificial breakage. Compare equivalent selections/snapshots and
gate-specific normalized identities; incomparable evidence is not convergence.

Escalation never means "ask the Architect to fix the code". It means the unit is
reported as a **contract defect**: the unit as specified cannot be satisfied by
this coder within the budget.

## Outer loop

The dossier crosses the boundary only when at least one unit is classified
`contract`. Implementation-classed units stay inside and are re-dispatched in the
same run.

| Control | Default | Rationale |
|---|---|---|
| `max_cycles` | 3 | past three revisions the contract is usually the problem, and a human should look |
| units added per rework | 2 | bounds growth so cycle budget cannot be diluted by scope expansion |
| `requested_changes` | advisory | only the Architect can assess feasibility |

## Budget

A run is bounded by three independent ceilings. Tripping any one ends the run with
reason `budget`, writing the dossier as normal so the Architect sees why.

| Ceiling | Value | Covers |
|---|---|---|
| Input tokens | 500k | context assembly is the dominant cost, not generation |
| Output tokens | 150k | |
| Cycles | 3 | |

The **formula** is core: worst case without a governor is `k × units × cycles`
coder calls, which at six units and `k = 3` is 54 calls per run. The **constants**
in the table above are the Unity adapter's starting point for a small project
(roughly $2–4 per run) and must be re-derived per stack.

The reason they cannot be shared: a Unity gate costs 60–120 s while `tsc --noEmit`
costs 2–5 s. The same `k` therefore means minutes of wall clock on one adapter and
seconds on another, and the token ceiling that governs a 40k-char C# context is
wrong for a stack with smaller units. Derive `k` from gate duration, and the token
ceiling from measured context size — not from this table.

## Termination

| Outcome | Condition | Repo state | Dossier |
|---|---|---|---|
| `awaiting_human_review` | full required suite and all gates pass, no unresolved contract defect | exact candidate retained; no constraint flush | none |
| `pass` | human approves exact candidate and completion provenance is finalized | cycle branch kept, accepted constraints flushed | none |
| `rework` | at least one `contract`-class failure, cycle budget remains | cycle branch kept | written |
| `abandon` | cycle budget or token budget exhausted | returned to start branch, cycle branches retained | written, with reason |
| `operational` | Unity missing, project locked, worker unreachable | untouched | none |
| `cancelled` | explicit cancellation | workers reconciled, candidates retained, starting user tree untouched | no manufactured contract dossier |

An operational failure aborts without consuming a cycle or a unit attempt. It must
never be reported as a unit failure, or the Architect will be asked to re-plan
against an infrastructure problem.

The run reservation survives waiting for review without holding a verifier/model
session. Human implementation findings resume bounded repair under the same frozen
version; presentation/requirement findings return a dossier for the next version.
Every changed candidate needs fresh verification and approval. Nonrunnable failures
return normal rework/operational outcomes, not an impossible visual review.

## Branch model

Each cycle commits to `agent/<run_id>/cycle-<contract_version>`.

- `abandon` restores managed integration state and leaves cycle branches for
  inspection. The user's starting branch/worktree is never switched or rewritten;
  external worktrees isolate execution. No forgotten git stash (D-25).
- Nothing is pushed. Nothing merges to a mainline branch without a human.

## Constraint flush

`learned_constraints` accumulate during a run but are only written to the managed
block in `AGENTS.md` on `pass`. A constraint emitted during a failed cycle is a
hypothesis and travels in the dossier instead.

Pass means human-accepted, not merely automated green (D-26). A metadata-only
completion revision must identify the approved parent and change no reviewed
source, test, asset, binding, requirement, or execution configuration.

Each entry must carry provenance: cycle confirmed, spec ref or criterion, and the
evidence that produced it. No provenance, no entry — a constraint that cannot
name its evidence is a situational observation, which is what rots into cargo
cult. Entries are keyed by a normalised hash of the statement so re-emission bumps
`confirmed` instead of duplicating.

Capped at 40 entries; overflow moves least-recently-confirmed entries to an
archive block rather than deleting them.

## Durable execution and recovery (D-25, D-27)

The operation journal records immutable intent before effects and reconciles
before/after revision identities with owner liveness. A live worker is waited on;
a completed application is not replayed; conflicting state stops recovery. Durable
test completion must match request/candidate identity. Run leases use OS guards,
require explicit stale reclamation, and can only be released by their owner.
Progress publishes an ordered log before its atomic snapshot; reconnect repairs
a lagging snapshot from that log. Cancellation records intent, reconciles the
owned worker, and retains the candidate without touching the starting user tree.

Record intent with unique operation ID, before/after snapshot identities, worker
ownership, and resource reservations before external effects. On restart reconcile
Git/filesystem and live processes with checkpoints. Never blindly replay patches,
reuse stale results, kill unrelated workers, or reclaim a live owner's lock.

Reserve model allowance before dispatch; reconcile actual usage afterward. Unknown
usage retains its reservation. Budgets, cycle consumption, and relevant repair
lineage survive migrations, restarts, and review. Version changes cannot reset
run accounting. Exhaustion stops further paid work and produces abandon evidence.

Provider rejections retain sanitized status, retry hints and upstream limit source
in the durable call record. Incomplete model content remains failure evidence,
never an executable patch. When a rejected response reports valid token usage,
charge it even though no patch is accepted; otherwise retain the full reservation.
Neither case automatically replays a paid call. Explicit upstream routing is part
of call identity, so a host-selected provider change cannot reuse an old call ID.
The optional upstream_provider setting pins one endpoint without changing model,
temperature policy or enabling fallback. The host may explicitly resume after
reconciliation while preserving earlier uncertain reservations.

status.json is atomically replaced; progress.jsonl has ordered sequence/time,
contract identity, per-unit stages, heartbeat, budgets, and verifier identity.
result.json, not log text or a heartbeat, establishes an invocation outcome.

## What to measure on the first real run

The offline retry component compares gate-specific failing identities, ignoring
diagnostic wording and ordering. Comparability requires equal contract, baseline,
environment, and selection identities. Incomparable failure requests explicit
review instead of claiming progress. A later gate is progress on comparable
inputs; returning to an earlier gate is regression. Attempt records retain TDD
stage separately from trend, and success does not reset accumulated regressions.

Owned snapshots bind unit, contract hash, snapshot ID, and exact owned contents.
Restoration rejects changed ownership, restores only implementation-owned paths,
and invalidates dependent/shared evidence. Atomic per-file writes do not claim
whole-candidate crash safety; the journal milestone must wrap those effects.
Dossiers are atomically written under the run directory, preserve mixed per-unit
classifications, and cannot emit implementation-only rework. Budget abandonment
may have no unit defects. `contract_sha256` explicitly names the digest algorithm;
`contract_sha` carries the same value for the original documented boundary.

Every number above is a defensible guess. These are the ones worth replacing with
data, in priority order:

1. **Ladder timing** — rung 3 and rung 4 wall clock. Sets whether the cycle budget
   is 8 minutes or 40.
2. **First-attempt pass rate** — how often a unit is green on attempt 1. If it is
   high, `k = 3` is generous; if it is near zero, the coder prompt is the problem,
   not the loop.
3. **Trend distribution** — the share of `PROGRESSING` vs `STALLED`. A high
   `STALLED` rate means units are underspecified, which is an Architect problem.
4. **Contract vs implementation split** — if most escalations are `contract`, the
   Architect is producing units that are too large or too vaguely specified.

## Open items

- `k = 3` and the token ceilings are unvalidated defaults pending the measurements
  above.

Review persistence distinguishes pending, accept, implementation, and contract.
Implementation findings produce a repair action in the same version; a fresh
verification request must precede another review. Contract findings require the
Architect's next version. Neither automatic green nor a submitted model identity
can authorize pass. Finalization checks the approved request and parent and rejects
source/asset/configuration changes in the completion snapshot. Budget continuity
and managed-constraint provenance remain governor responsibilities.

The branch component journals abandonment before detaching the clean managed
integration worktree to its baseline. It retains the cycle ref at the candidate,
rejects dirty or foreign state, and reconciles an interrupted detach on restart.
The starting user worktree is never switched, stashed, or cleaned.

Accepted constraint preparation checks the approved candidate, version and
original AGENTS.md hash. Its marked JSON block retains active and archived
entries with normalized statement hashes and confirmation provenance. It changes
no bytes outside that block. Metadata completion builds a separate Git index,
checks the exact approved parent and complete expected tree, records intent,
then publishes the cycle ref with compare-and-swap. Recovery reuses that commit;
conflicting worktree bytes or journal content stop before publication. These are
tested components. BudgetGovernor now connects persistent dispatch stop, worker
reconciliation, retained branches and a budget abandon dossier. It refuses to
detach while workers remain unreconciled and retains the exhaustion snapshot so
late usage reconciliation cannot reopen the run or change dossier provenance.
The production graph must still invoke these components through its full lifecycle.

## Production effect reconciliation

The production driver now connects these lifecycle components. It publishes
activity, attempts and active verification identity with an in-flight heartbeat;
the heartbeat stops at stage exit. Trusted cancellation intent prevents subsequent
dispatch and candidate admission while existing calls settle and retain receipts.

Stage checkpoints and per-effect intents record fixed coding plans, worker and
review results, candidate before/expected/after trees, and verification receipts.
Restart reuses proven completed effects, including regression restoration and
metadata completion. Unknown paid results require explicit owner/usage
reconciliation; no retry silently resets budget. Conflicting commits or ambiguous
dirty worktrees remain fail-closed and are never automatically reset.
