# Boundary contract: Architect ⇄ LangGraph

The single source of truth for what crosses the line, in which direction, and who
decides what. Anything not written here does not cross.

Supersedes every earlier sketch of the pipeline.

Current authority: D-19 through D-27 extend or supersede the original decisions.
The Architect is Codex with OpenSpec. It delegates apply and retains planning,
contract revision, task reconciliation, specification verification, and archive.

## Decisions on record

| # | Decision | Consequence |
|---|---|---|
| 1 | The contract lives in the repo | Graph reads exported specs and approved hashed profiles; owned code/test writes and run artifacts are permitted. AGENTS.md is its sole managed convention write. |
| 2 | Ownership is immutable within a cycle | `owns` may not be added to, removed from, or reassigned for a surviving unit mid-cycle. |
| 3 | `judge` classifies the defect | The judge receives the spec, not just test results. Backed by a deterministic escalation rule. |
| 4 | The Architect may add units on rework | Only when revision is infeasible or uneconomical, and only with recorded justification. |
| 5 | Confirmed constraints persist into `AGENTS.md` | One managed block. Flush requires human acceptance and provenance. |
| 6 | Tests are authored and frozen before implementation | Two-phase cycle. Frozen test files are a second immutability set. |
| 7 | Verification is a ladder, Unity is only the last rung | Compile does not need Unity. Attribution comes from the ladder. |

## Artifact 1 — the contract (forward)

Lives at `specs/<NNN-feature>/contract.v<N>.json`, next to `spec.md`, relative to
the target game repository. Written by the Architect, read-only to the graph.
The JSON below introduces the unit vocabulary; the complete current illustrative
wire format is in `contracts/queue-reorder.example.json` in the framework repo.
All runtime loaders validate format_version, links, declared role scopes, and
profile references as well as the unit fields.

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
- `status` is `active` or `superseded`. Units are never removed between cycles.
  Superseded claims remain history; explicit migrations can transfer current
  ownership to active units at a version boundary under D-20.
- `module_root` bounds implementation scope. `test_roots` separately declares
  permitted test scope; every owned path must be inside its role's scope and the
  independent target game boundary. New units require add_justification. No role
  can claim specs, planning, profiles, protected presentation, or shared host paths.
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
3. **Additions and migrations occur between versions only.** Newly claimed paths
   fill unclaimed role scope unless an explicit ownership_migrations entry names
   the prior owner, active destination, paths, and rationale. Validate the whole
   current map, reject collisions and orphaning, retain history and run budgets.
4. **Supersede, never remove.** Retiring a unit sets `status: "superseded"`. Its
   historical claims remain recorded; current ownership must be fully accounted
   for, including explicit transfers. Frozen tests never migrate to impl roles.
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
temperature 0 by default. D-28 permits an explicitly approved provider-controlled
temperature policy for the configured judge; this omits the temperature parameter
and retains the requested reasoning effort. It never activates as an automatic
fallback after a failed request.

**Bias control.** Coder and judge are different models, and the judge sees no
self-justification. Self-assessment inflates pass rates; the separation is cheap.

**Deterministic backstop.** A model judgement alone is unsafe authority here: a
judge that keeps saying `implementation` traps the coder on a unit that can never
converge. The graph therefore applies a rule that does not depend on judge
quality:

> STALLED escalates immediately; first REGRESSED restores safe state and permits
> one retry within budget; second regression or failed-attempt exhaustion escalates
> regardless of the judge. See D-23 and loop-control.md.

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
- Graph → Architect: coder notes, raw Unity logs, or authorship signals. Structured
  attempt summaries and candidate/evidence references are allowed; raw patch dumps
  are not required for the dossier. The Architect can review the candidate itself.

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

The invocation identifies `(contract, run_id)` plus hashed baseline/profile inputs.
Durable journals, budgets, and prior contract identities are explicit recovery
state, not hidden conversational state. A resumed invocation reconciles them.

## Current wire additions and worked boundaries

The Phase 1 loader consumes UTF-8 JSON bytes and a repository root plus adapter
path rules. `spec_sha256` identifies the bytes at `spec_ref`; each profile ref
contains `path` and `sha256`. All digests are lowercase 64-character SHA-256.
The illustrative example uses placeholder digests and is intentionally not a
runnable bundle. Supply actual exported files and hashes before invocation.

For v2, include `previous_contract_sha256` equal to the validated v1 byte hash.
Replaying the same version requires identical bytes and revalidates referenced
inputs. New versions must be consecutive. Run-owned cycle/growth limits are
passed independently; the contract cannot raise them. `lineage_for(unit_id)`
preserves predecessor IDs for subsequent resource/history accounting, rather than
resetting it during migration. Durable accounting itself is a later phase.

- `format_version` is wire compatibility; `contract_version` is the cycle. Require
  consecutive revisions and immutable bytes for a previously seen version.
- `task_links` map stable OpenSpec task IDs to unit IDs and criteria. `test_links`
  name test ID, author unit, implementing units, and criterion. A shared test can
  require several units; its name does not uniquely attribute blame (D-22).
- `presentation_ref`, `coding_profile_ref`, and `environment_ref` carry relative
  artifact paths and SHA-256 identities. Resolve design/wiki conflicts before
  export; mechanically enforce profile rules through the selected adapter.
- `ownership_migrations` carry from_unit, to_unit, paths, and rationale. Newly
  added units require recorded justification and retain growth limits.

| Example | Result |
|---|---|
| Impl owns Runtime/Script/Queue.cs under module_root Runtime/Script | Valid if unclaimed and target policy permits |
| Test owns Tests/Runtime/Script/QueueTests.cs under declared test_roots | Valid independently of production module_root |
| Two active units own the same normalized path | Reject using adapter comparison rules |
| Unit owns specs/feature/contract.v1.json or ../shared/Utility.cs | Reject even if a contract declares it |
| v2 supersedes U1 and explicitly transfers A.cs to U2 | Valid if path, role, scope, justification, and budget checks pass |
| v2 omits U1 or silently transfers its path | Reject; history is never removed |

## Execution, observation, and human review

### Portable target profile

The profile uses `host_selector: "UNITY_HOST"`, `game_selector: "GAME_ROOT"`,
and an `allowed_mount` such as `Assets/JJGame/monopoly`. Actual locations are
resolved from machine configuration, never stored in the JSON. The caller supplies
an independently authorized mount plus implementation/test root bounds. A profile
may narrow these bounds but cannot expand them. Source entries carry a stable
`source_id`, relative `path`, and `sha256`; rule entries carry path/hash. Both are
verified from the module checkout before use and are protected from ownership.

`TargetProfile.validate_contract` requires the contract's coding-profile hash to
match and intersects every active ownership claim with the profile's role scopes.
For example, `Runtime/Script/Game.cs` may be permitted, while
`Packages/manifest.json`, a sibling module claim, or a generated sidecar outside
the authorized module scope is rejected. Full host fingerprint/materialization
checks remain the worker's later responsibility.

The coordinator publishes status.json and progress.jsonl under
.agent/runs/<run_id>/ in its external workspace. result.json distinguishes
awaiting_human_review, rework, abandon, operational, cancelled, and accepted pass.
Include format, run/contract/hash, candidate, evidence refs, and reason. Progress
never proves completion or changes a frozen contract. Contract rework ends the
invocation with a dossier; implementation repair remains in execution.

Human review records exact candidate/baseline/contract identities, reviewer,
decision, and findings. Existing-contract bugs return for bounded implementation
repair. Design/layout changes require the Architect's next contract version.
Only accepted pass permits constraint flush and planning-task reconciliation.

## Open items

Nothing in this document is blocking. `k = 3` and the cost ceilings referenced in
`loop-control.md` are unvalidated defaults; the consolidated list of open items
lives at the end of `decisions.md`.

### Presentation and review component formats

The generic Presentation manifest hashes its baseline revision, protected file
references, interfaces, entry points, permitted binding/action pairs, artist
requirements, reused content, and launch instructions into one identity. It
validates protected bytes before distributing them unchanged; conflicting existing
files are rejected. Unity reports import identities, missing scripts, unresolved
bindings, and loaded review entries against that identity, then checks serialized
interfaces through the structural adapter. Offline reports are test seams, not
proof that a scene was imported or played in a real editor.

ReviewGate consumes full-suite VerificationResult evidence for its exact run and
contract. A trusted host authentication callback supplies human identity; model
file tools must never expose that callback or the review gate. Credentials are not
persisted. review.json records the complete verification request, file hashes,
evidence references, reviewer, decision, findings, and timestamp. Prior review
records are retained under the run's reviews/ directory when a new verified
candidate is offered. Progress reconnect can read this record without approving it.

Completion requires the approved parent and identical reviewed files, with only
AGENTS.md eligible for the later managed-constraint writer. That writer must still
validate provenance and preserve all unrelated content. These components do not
replace the runtime integration, trusted UI, or real editor acceptance checks.

### Delegated planning boundary component

`discover_context` consumes the selected existing project's pinned OpenSpec apply
JSON. Artifact IDs and concrete files come from its active schema; no second
planning root or custom schema is required. Explicitly selected design, wiki and
rule sources are exported with relative paths and hashes. Absolute CLI locations
are accepted only within that selected root and converted to portable references.
Task IDs are namespaced as `<change>:<id>` and checked against their current
source line and checkbox. Prompt context and guidance remain Architect inputs,
not copied execution instructions or proof of completion.

For example, a queue change can map `queue-reorder:1.1` to its test author, state
unit and system unit. The Architect exports source provenance and validates the
contract, then creates an ArchitectBoundary with an external trusted state root.
Its blocking executor callback receives start initially, resume when durable
progress exists, repair after an implementation finding, or finalize after human
acceptance. The callback owns the lease and all actual execution gates. The
boundary ignores callback return values and reads the durable result instead.

Full-suite readiness still returns awaiting_human_review. A pending review does
not dispatch. A human contract finding returns rework to the Architect; a human
implementation finding keeps the existing contract. Only a persisted pass with
the matching accepted review and approved parent produces advisory eligible task
IDs. An unrelated task, such as `queue-reorder:1.2`, remains unmapped and incomplete.
The Architect inspects all mapped evidence, rediscovers task locations and updates
planning itself. Source hashes are checked before and after execution so a changed
planning file cannot silently become the accepted planning baseline.

This component trusts the host-owned run-state directory and does not authenticate
human sessions. ReviewGate and CandidateCompletion remain responsible for that
gate and actual Git ancestry. The local CLI exports context and observes results;
`invoke_local(boundary, executor)` connects the Architect to the exported graph.
The trusted host supplies ProductionExecutor with its held lease, run budget and
LocalExecutionServices. Services connect isolated worktrees, independent test
review, frozen TDD, model calls, the adapter verifier, retry policy and human gate.
Neither contract JSON nor a serialized API request can construct these services.
Target/presentation preflight and human authentication remain trusted host inputs.

The graph checkpoints prepare, Red, code, verify, Refactor, final verification,
review and finalization. Coding callbacks overlap; integration and verification
are sequential. Only completed service receipts are automatically reused. An
interrupted effect without a receipt requires host reconciliation. An operational
stop can explicitly resume its failed stage without repeating completed preparation
or resetting token reservations. This is not permission to replay an uncertain
paid request under the same call ID.

For a worked second cycle, suppose the human rejects queue layout in v1. Local
invocation consumes that authenticated decision and records a per-unit rework
dossier. The Architect revises the design/export and validates contract.v2.json
against v1. With the same run lease and reconciled workers, `transition_cycle`
records its intent, adds the consecutive version to the existing budget ledger,
archives v1 invocation/result/review/status records under cycles/v1/, and publishes
the v2 identity. Progress sequence continues across both versions; token usage,
unit lineage, dossiers and cycle branches remain. Interrupted transitions replay
their recorded state changes idempotently. Only after this transition does the
Architect construct the v2 boundary and executor. After exact-candidate acceptance,
task reconciliation still belongs solely to the Architect.

Offline real-Git tests exercise these paths. The live exported graph reached five
expected Red failures on the isolated Unity fixture, then stopped on model transport.
After explicit same-model provider routing and preserved-budget reconciliation,
that same run passed five Green tests and five final Refactor-confirmation tests,
and offered the exact candidate for human review. This is isolated diagnostic
evidence, not acceptance of the game's UI baseline or its deferred existing tests.
Real human acceptance remains outstanding.

### Production review guidance and confirmed constraints

Every LocalExecutionServices review offer now supplies a ReviewPackage bound to
its complete VerificationRequest. The package records code/visual scope, entries,
launch instructions, required interactions, visual references and placeholder
limitations. Paths must belong to the reviewed snapshot. A visual package requires
entries and references; missing guidance or a stale request is rejected. The same
request cannot silently replace its package. ArchitectBoundary.observe and the
status CLI expose review_package on reconnect.

The default package uses the hashed Architect presentation manifest's entries,
instructions and asset references. An empty presentation object explicitly denotes
a code-only contract; its review asks the human to inspect the specification and
mapped criteria and makes no visual acceptance claim. Hosts can supply a typed
review_package callback for richer instructions. The callback is trusted host
composition, never a model-controlled service selector.

After authenticating exact-candidate acceptance and before resuming finalization,
the trusted host may call services.confirm_constraints(request, entries), where
entries is a tuple of LearnedConstraint values. Each entry must carry confirmed
version, criterion and evidence provenance accepted by the existing constraint
validator. The collection is persisted immutably, is safe to confirm identically
again, and is rejected for pending/stale approval, changed entries or completion
already underway. Empty completion remains valid when no learned entries exist.
Completion and crash recovery consume the same persisted collection under a guard;
confirmation cannot race past the selection of entries. The metadata-only parent,
managed-block preservation, deduplication and archival checks remain mandatory.
