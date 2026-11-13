# Boundary contract: Architect ⇄ LangGraph

The single source of truth for what crosses the line, in which direction, and who
decides what. Anything not written here does not cross.

Supersedes every earlier sketch of the pipeline.

## Decisions on record

| # | Decision | Consequence |
|---|---|---|
| 1 | The contract lives in the repo | Graph reads `specs/` only. Sole repo write: the managed block in `AGENTS.md`. |
| 2 | Ownership is immutable within a cycle | `owns` may not be added to, removed from, or reassigned for a surviving unit mid-cycle. |
| 3 | `judge` classifies the defect | The judge receives the spec, not just test results. Backed by a deterministic escalation rule. |
| 4 | The Architect may add units on rework | Only when revision is infeasible or uneconomical, and only with recorded justification. |
| 5 | Confirmed constraints persist into `AGENTS.md` | One managed block. Flush is gated on a green run and on provenance. |
| 6 | Tests are authored and frozen before implementation | Two-phase cycle. Frozen test files are a second immutability set. |
| 7 | Verification is a ladder, Unity is only the last rung | Compile does not need Unity. Attribution comes from the ladder. |

## Artifact 1 — the contract (forward)

Lives at `specs/<NNN-feature>/contract.v<N>.json`, next to `spec.md`. Written by
the Architect, read-only to the graph.

```json
{
  "contract_version": 1,
  "module": "queue-manipulation",
  "module_root": "Assets/_Project/Scripts/Queue/",
  "spec_ref": "specs/003-queue-manipulation/spec.md",
  "units": [
    {
      "id": "U1-state",
      "role": "impl",
      "status": "active",
      "title": "Reducer support for queue reordering",
      "spec_ref": "R7-queue-reorder",
      "owns": ["Assets/_Project/Scripts/Queue/DinerState.cs"],
      "acceptance": ["QueueReorderTests.Reorder_PreservesCustomerIdentity"],
      "depends_on": [],
      "interfaces": [
        { "symbol": "DinerActions.ReorderQueue", "signature": "ReorderQueue(int from, int to)" }
      ],
      "instructions": "Add a ReorderQueue action and reducer case."
    },
    {
      "id": "U0-tests",
      "role": "test",
      "status": "active",
      "title": "EditMode coverage for reorder",
      "spec_ref": "R7-queue-reorder",
      "owns": ["Assets/_Project/Tests/EditMode/QueueReorderTests.cs"],
      "acceptance": [
        "QueueReorderTests.Reorder_PreservesCustomerIdentity",
        "QueueReorderTests.Reorder_FromEmptyQueue_IsIgnored"
      ],
      "depends_on": [],
      "interfaces": [],
      "instructions": "Write failing tests from the spec scenarios. Do not touch production code."
    }
  ]
}
```

**Field notes**

- `role` drives the two-phase gate. Units with `role: "test"` are dispatched in
  phase A and their files are frozen at the phase boundary; `role: "impl"` units
  run in phase B and may not touch frozen files. The graph never guesses which
  files are tests — the contract declares it.
- `status` is `active` or `superseded`. Units are never removed between cycles;
  a retired unit's files stay in the ownership map so nothing is orphaned.
- `module_root` bounds decision 4. An added unit must live inside it, otherwise
  "add a unit" becomes a backdoor to scope creep across the project.
- `depends_on` and `interfaces` are Architect-only knowledge. The graph cannot
  infer that U1 needs a symbol U0 introduces. Without `interfaces`, dependent
  units must be serialised; with them they can run in parallel against a
  declared signature.
- `contract_version` **is** the cycle number. There is no separate cycle counter
  in graph state, so "one bump per cycle" is enforced by the file rather than by
  convention, and a crash cannot double-increment it.

## Artifact 2 — the dossier (backward)

Written to `.agent/runs/<run_id>/dossier-v<contract_version>.json`, outside the
tracked spec tree so it never pollutes repo history.

```json
{
  "dossier_version": 1,
  "run_id": "2026-11-12T14-02-11",
  "cycle": 2,
  "contract_version": 2,
  "contract_sha": "a1b2c3d",
  "verdict": "fail",
  "failed_units": [
    {
      "id": "U3-tests",
      "defect_class": "contract",
      "criterion": "R7-queue-reorder",
      "gate": "tests",
      "evidence": {
        "type": "test",
        "ref": "QueueReorderTests.Reorder_PreservesCustomerIdentity",
        "message": "expected patience 3 at id c2, got 0"
      },
      "hypothesis": "reducer reindexes patience by position",
      "attempts": 3,
      "history": ["RED", "RED", "REGRESSED"]
    }
  ],
  "learned_constraints": ["DinerState is immutable; mutations go through reducers"],
  "requested_changes": [
    { "kind": "revise", "unit": "U3-tests" },
    { "kind": "add", "for_criterion": "R7-queue-reorder" }
  ],
  "budget_remaining": 1
}
```

**Field notes**

- `defect_class` is **per unit**. One cycle can contain an implementation defect
  in U1 and a contract defect in U3 simultaneously; a dossier-level verdict
  forces a binary choice that does not exist.
- `gate` names the rung that failed (`ownership`, `conformance`, `compile`,
  `tests`), so the Architect knows how deep the failure went without reading logs.
- `history` is the attempt trend: `RED`, `PROGRESSING`, `STALLED`, `REGRESSED`.
- `requested_changes` is **advisory**. The Architect may decline a suggested
  `add` and revise instead, provided justification is recorded either way — only
  it can assess feasibility.
- `contract_sha` makes a run reproducible: it names the exact contract bytes that
  produced this dossier.

## Ownership and immutability

Derived from decisions 2, 4 and 6, which interact:

1. **Frozen ownership map.** At `partition`, the graph snapshots
   `{unit_id -> owns}`. Before every write it re-checks the map. Freezing is
   bidirectional: adding a path is as illegal as removing one, because removing
   a path orphans files already written this cycle.
2. **Frozen test set.** At the end of phase A, every file owned by a
   `role: "test"` unit becomes immutable for the rest of the cycle. Any patch
   touching a frozen file is rejected by `integrate`, never repaired. This is
   what makes the TDD gate structural rather than a prompt instruction.
3. **Additions fill unclaimed space.** A new unit's `owns` must be disjoint from
   the frozen map and inside `module_root`. A new unit claiming an existing
   unit's file is a mutation wearing a new ID: hard reject.
4. **Supersede, never remove.** Retiring a unit sets `status: "superseded"`. Its
   files remain owned.
5. **`specs/` is never valid in `owns`.** Mechanically enforced. The graph must
   not be able to write its own instructions.
6. **One version bump per cycle.** `contract_version` advances exactly at a cycle
   boundary, never mid-cycle.

## Defect classification

The judge is a **router between two loops**, not a pass/fail gate.

**Inputs it must receive:** acceptance criteria, mechanical evidence (gate that
failed, compile errors, failing test names, assertions), the spec excerpt, the
ownership map, and the full text of the patched files (the diff under review).

**Inputs it must not receive:** the coder's `notes`, which coder produced what,
or any authorship signal. It runs on a different model from the coder, at
temperature 0.

**Bias control.** Coder and judge are different models, and the judge sees no
self-justification. Self-assessment inflates pass rates; the separation is cheap.

**Deterministic backstop.** A model judgement alone is unsafe authority here: a
judge that keeps saying `implementation` traps the coder on a unit that can never
converge. The graph therefore applies a rule that does not depend on judge
quality:

> Escalate the unit to `defect_class: contract` when its attempt history reaches
> `STALLED` or `REGRESSED` per `loop-control.md`, regardless of the judge.

## Loop responsibility

| | Inner loop | Outer loop |
|---|---|---|
| Owner | LangGraph | Architect |
| Handles | `defect_class: implementation` | `defect_class: contract` |
| Mechanism | Re-dispatch the unit with error text in context | New `contract.v<N+1>.json` |
| Bound | `k = 3` attempts per unit | `max_cycles = 3` |
| Crosses boundary | No | Yes: dossier out, contract in |

## Never crosses

- Architect → graph: preferred implementation approach, reasoning traces,
  conversation history, execution hints ("run these in parallel").
- Graph → Architect: patches, coder notes, raw Unity logs, retry counters.

Trust is asymmetric by design. The graph treats the contract as untrusted input
and validates it. The Architect treats `hypothesis` as a guess and `evidence` as
fact.

## How the outer loop is driven

Because the contract lives in the repo, the graph does not poll for a response.
It finishes the cycle, writes the dossier, exits, and the next run is invoked
with the new contract path:

```
python -m unity_coder.graph --contract specs/003-.../contract.v3.json --run-id <same run>
```

The graph is therefore a pure function of `(contract, run_id)`. Outer-loop
attribution is one diffable file per cycle, with no hidden state crossing the
line.

## Open items

Nothing in this document is blocking. `k = 3` and the cost ceilings referenced in
`loop-control.md` are unvalidated defaults; the consolidated list of open items
lives at the end of `decisions.md`.
