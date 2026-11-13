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
| `STALLED` | retry if `attempt < k`, else escalate as `contract` |
| `REGRESSED` | restore the unit's owned files from its pre-apply snapshot, retry once with the regression diff; a second `REGRESSED` escalates as `contract` |
| any, `attempt == k` | escalate as `contract` regardless of trend |

`k = 3`. Two rules override the judge, and both exist because a model that
misclassifies as `implementation` would otherwise trap the coder on a unit that
can never converge:

1. `STALLED` or `REGRESSED` at any point escalates to `contract`.
2. Attempt exhaustion escalates to `contract`, unconditionally.

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
| `pass` | all gates green, judge classifies nothing as `contract` | cycle branch kept, constraints flushed | not written |
| `rework` | at least one `contract`-class failure, cycle budget remains | cycle branch kept | written |
| `abandon` | cycle budget or token budget exhausted | returned to start branch, cycle branches retained | written, with reason |
| `operational` | Unity missing, project locked, worker unreachable | untouched | none |

An operational failure aborts without consuming a cycle or a unit attempt. It must
never be reported as a unit failure, or the Architect will be asked to re-plan
against an infrastructure problem.

## Branch model

Each cycle commits to `agent/<run_id>/cycle-<contract_version>`.

- `abandon` returns the working tree to the start branch and leaves the cycle
  branches for inspection. Nothing half-applied, nothing lost, and no `git stash`
  that can be forgotten.
- Nothing is pushed. Nothing merges to a mainline branch without a human.

## Constraint flush

`learned_constraints` accumulate during a run but are only written to the managed
block in `AGENTS.md` on `pass`. A constraint emitted during a failed cycle is a
hypothesis and travels in the dossier instead.

Each entry must carry provenance: cycle confirmed, spec ref or criterion, and the
evidence that produced it. No provenance, no entry — a constraint that cannot
name its evidence is a situational observation, which is what rots into cargo
cult. Entries are keyed by a normalised hash of the statement so re-emission bumps
`confirmed` instead of duplicating.

Capped at 40 entries; overflow moves least-recently-confirmed entries to an
archive block rather than deleting them.

## What to measure on the first real run

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
