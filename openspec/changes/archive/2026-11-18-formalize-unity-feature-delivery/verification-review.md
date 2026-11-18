# OpenSpec verification review — 2026-11-18

## Follow-up disposition

The user-authorized implementation follow-up resolves W1, W2 and W3 below.
Eleven new frozen regressions and the updated evidence in verification.md cover
retained counters, complete review guidance/Architect reconnect, and nonempty
accepted-constraint completion/recovery. There are no remaining warnings among
those three findings. The original report below is retained as historical evidence.

The independent-judge requirement-length suggestion remains. Combined live
acceptance and an actual simultaneous coding/waiting/refactoring scheduler
rehearsal remain outside this follow-up's verified evidence; coding/verification
overlap was previously verified. No unqualified archive-readiness claim is made
from task counts alone. These evidence limits do not create new archive policy.

Change: formalize-unity-feature-delivery. Schema: superpowers.
Revision: 11c4b574d6538f01a8cb37cb1c6b243f3905c533, with local README/QUICKSTART
documentation changes. This advisory review changes no implementation, tests,
task checkboxes or archive state. It supplements the earlier compliance review;
the findings below qualify its production-completeness conclusions.

## Scorecard

| Dimension | Result |
|---|---|
| Completeness | 61/61 tracked tasks; all five artifact groups present. Four delta specs contain 44 ADDED requirements and 69 scenarios; no removals or renames. Implementation locations are identified for all 44 in compliance-review.md; three production-wiring divergences are recorded below. |
| Correctness | Requirement mapping inspected against production review/completion/progress code and the prior coverage matrix. 38 focused tests pass. Scenario Coverage is partially verified: existing component coverage does not establish the richer production review package or nonempty production constraint flush, and the exact simultaneous coding/waiting/refactoring scenario lacks a production demonstration. |
| Coherence | Core/adapter separation, immutable contracts/tests, external worktrees, blocking verification and human-gated completion follow the design. Three warnings concern incomplete connections between those components. Code Pattern Consistency checked; no additional significant pattern issue identified. |

## Evidence and method

- Pinned CLI status reports planning complete; apply reports all_done, 61/61,
  with no unavailable tracking files. These are inventory facts, not correctness
  verdicts. Proposal capability names match all four spec files.
- Inputs: brainstorm, proposal, design, tasks, four capability deltas, authoritative
  docs and handoff, compliance-review.md, final verification and live receipts.
  The earlier requirement matrix remains the reference for implementation
  locations across all 44 requirements; this pass checks the production connections
  it previously treated as covered by component evidence.
- All 69 frozen-test hashes and 125 reviewed-file hashes match. The prior full
  suite result, 468 passed in 144.12 seconds, is applicable to these unchanged
  implementation bytes. It was not rerun wholesale during this advisory review.
- Fresh command: `uv run pytest -q tests/test_executor_review_resume.py
  tests/test_completion.py tests/test_constraints.py tests/test_human_review.py`.
  Exit 0: 38 passed, one existing TestResult collection warning, 28.58 seconds.
- A disposable offline diagnostic invoked the existing fixture factories and
  production graph without editing frozen tests. At awaiting_human_review,
  `status.attempts` was `{}` while services retained all three unit counters.
  The review record contained only request, candidate_revision, files,
  evidence_refs and decision. A wrapper observed the actual finalization call:
  outcome pass, learned-constraint entry count 0. No model or Unity call occurred.
- Existing tests demonstrate authentication, stale-candidate rejection, repair
  routing, metadata-only completion, managed-block provenance and archive limits.
  Passing these tests does not cover the specific missing connections below.

## Critical issues

None identified: no unchecked task or wholly absent requirement implementation
was found. Partial implementation divergences are warnings rather than claims
that the underlying components do not exist.

## Warnings

### W1 — Stage completion discards attempt counters from current status

Requirement: execution-lifecycle / Architect can observe execution without
controlling it. Records must include per-unit attempts.

`src/unity_coder/core/executor.py:176` publishes the final stage transition without
attempts. `src/unity_coder/core/progress.py:77` defaults omitted attempts to `{}`.
The heartbeat does publish counters, but that record is replaced at stage exit;
at review or terminal outcomes it is the empty-counter record that persists.
This was reproduced through the production graph. The existing production
observation test checks counters only while verification is blocked.

Recommendation: pass the service counter snapshot into the post-stage publication
and add frozen regressions for counters after a failed attempt, stage transition,
and terminal/review result. Preserve counters on reconnect as well.

### W2 — Production review handoff omits required presentation guidance

Requirement: execution-lifecycle / Automated success waits for human acceptance.
The review package must identify launch instructions, required interactions,
visual references and placeholder limitations as well as candidate/test identity.

`src/unity_coder/core/review.py:63` writes hashes and test-evidence references.
`src/unity_coder/core/local_executor.py:539` offers that evidence without a review
package or presentation-manifest reference carrying the guidance. The generic
Presentation object contains instructions and assets, and the visual demo supplies
manual documentation, but the production handoff does not assemble or validate
that information. A presentation digest alone does not tell the reviewer what to
launch and inspect. The diagnostic confirmed the emitted record fields.

Recommendation: expose a validated, candidate-bound presentation review package
or portable reference in the production offer. Include launch, interactions,
visual references and placeholder limits; reject absent or stale metadata.
Add a production test verifying the package survives observation/reconnect.

### W3 — Production finalization cannot flush nonempty learned constraints

Requirement: execution-lifecycle / Accepted completion preserves provenance;
design section 8 and Phase 7 managed-constraint delivery.

`src/unity_coder/core/local_executor.py:543` calls CandidateCompletion.complete
with `()` unconditionally. The recovery completion path also supplies `()`.
CandidateCompletion and accepted_constraints support actual LearnedConstraint
entries, but LocalExecutionServices has no input or durable collection feeding
them into this path. The graph can produce pass without ever delivering learned
entries. Empty completion is valid when there are none; it cannot demonstrate
delivery when accepted evidence does contain learned constraints.

Recommendation: provide a trusted, validated, persisted collection of confirmed
entries and use the same identity during completion/recovery. Add a production
test approving a candidate with one learned entry, checking the managed block and
provenance, and recovering an interrupted completion without duplicating it.
Keep the existing component provenance/deduplication tests unchanged.

## Suggestion

S1: the independent-judge requirement in architect-execution/spec.md exceeds the
CLI's 500-character guideline. Normal OpenSpec validation passes; strict mode
reports this known warning. If the requirement is deliberately revised later,
split its distinct behaviors into requirements/scenarios while preserving D-28
and judge independence. Do not silently rewrite the frozen requirement just to
suppress a validator warning.

## Applicable checks not fully verified

- Scenario Coverage: missing production assertions for W2/W3, and no production
  test showing one unit coding while another waits and a third refactors. Existing
  tests establish coding/verification overlap and component state representation,
  which are narrower evidence. Add a controlled multi-unit scenario or explicitly
  establish the intended scheduler behavior in a subsequent implementation review.
- Live combined acceptance: the model-driven candidate still awaits human review;
  live accepted metadata completion and post-fix crash/cancellation/migration
  rehearsal remain unverified. Separate lake-demo approval cannot establish them.
  These are limits of the available evidence, not new archive prerequisites.
- Original Monopoly suite acceptance is intentionally outside this verification;
  its known failures remain deferred and neither its code nor its tests were run
  or changed. Automated PlayMode, remote workers and other adapters are outside
  the change's scope, not skipped required checks.

## Assessment

No critical issues found in the checks that ran. Three warnings and one suggestion
remain. Scenario Coverage and combined live acceptance are not fully verified for
the reasons above; this report does not assert unqualified archive readiness.
No implementation fix, spec synchronization, archive, commit or push was performed.
