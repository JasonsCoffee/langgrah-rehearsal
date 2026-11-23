# Tasks

Apply authorized by the user after the optimizer result/report refinement. Paths named `H/` below are shorthand for
`openspec/changes/rehearse-monopoly-game-lobby/` inside the existing isolated
backend checkout; `P/` means
`openspec/changes/direct-deepseek-context-optimization/` in the selected planning
store. `R/` means the externally selected `LOBBY_RUN_ROOT`; `S/` means its
`trusted-state/` directory. These are named path selectors, not new directories
under Unity imports. All `tests/` and `src/` selectors refer to the isolated
backend checkout. No task edits shared framework runtime or existing frozen tests.

## 1. Preserve and reconcile the existing execution boundary

- [x] 1.1 Inspect `R/trusted-state/.agent/runs/monopoly-game-lobby/result.json`, `status.json`, `budget.json`, `executor-v70.json`, `services-v70/effects/` and `S/current-execution.json`; record current candidate/contract, live owners, every unresolved call and reservation in `P/migration-inventory.md`. Verify the record against Git HEAD, ledger totals and full call-set hashes without invoking models or changing state.
- [x] 1.2 Verify the existing isolated branch has a saved checkpoint before implementation edits and document its revision in `P/migration-inventory.md`; inspect `git status --short` and preserve user changes. No mainline commit, automatic cleanup, push or merge.
- [x] 1.3 Verify the 199-file freeze inventory, original host baseline identity and pinned `H/trusted_overlay.py` / `H/overlay_host.py` hashes against their trusted records; record exact equality in `P/migration-inventory.md`. Any drift blocks activation; no restoration or rewritten hash is permitted by this task.
- [x] 1.4 Read the newly stopped operation's exact failed receipts, claims, sanitized diagnostics and completed effects; specify a proof-bound fresh-ID recovery in `P/migration-inventory.md`. Verify no active process or uncertain effect will be replayed, and include all reservations beyond the previously registered 26 if present.

## 2. Freeze independent host tests before implementation

- [x] 2.1 Author new offline tests in `tests/test_direct_deepseek_host.py` and `tests/test_mixed_role_policy.py` for direct dialect, endpoint/secret safety, every Coder stage at low, Judge low, model identity, all usage paths and historical medium-policy validation. Use fake transports; verify meaningful failing assertions against the current implementation with `uv run pytest -q tests/test_direct_deepseek_host.py tests/test_mixed_role_policy.py`.
- [x] 2.2 Author `tests/test_evidence_packet_manifest.py` and `tests/test_evidence_selection_guard.py`, with at least twelve independently specified fixtures in `tests/fixtures/context_optimization/`. Cover unified optimized-input/check-results output, verified versus model-reported checks, fallback/blocked decisions, required full files, test helpers, partial classes, dynamic dependency fallback, exact spans/Unicode, cross-owner causes, duplicate failure multiplicity, injection, changed candidate and unauthorized verdict text. Verify observed failing assertions with the corresponding focused pytest command.
- [x] 2.3 Author `tests/test_context_accounting_recovery.py`, `tests/test_judge_context_expansion.py` and `tests/test_architect_finding_index.py` for uncertain calls, bounded expansion, no silent replay, same-run migration, exact verdict preservation and inaccessible-reference hydration. Verify meaningful Red with focused pytest; do not use paid calls or Unity.
- [x] 2.4 Record all new fixture/test hashes, independent expected findings, complete intended coverage and Red outputs in `P/test-freeze.md`; freeze this host-test set before helper implementation. Verify no old offline test or any of the 199 lobby files changed. Test defects return to planning rather than implementer edits.

## 3. Implement direct provider and mixed role policy

- [x] 3.1 Implement `H/direct_deepseek_client.py` with the existing client interface, local ignored `ai.local.toml` key reference, explicit `thinking.type=enabled`, `reasoning_effort=low`, `max_tokens`, strict completion validation, normal TLS and redirect refusal. Verify frozen request/response/secret tests pass, including charged truncation and unknown-usage retention; update `P/provider-migration.md` with the exact request policy.
- [x] 3.2 Implement `H/mixed_backend_policy.py` and its portable proposed role profile, separating direct Coder/selector and Codex Judge low. Update only the active composition in `H/lobby_production_host.py`; preserve historical grants. Verify all stages and format repairs route correctly with `tests/test_mixed_role_policy.py` and mocked model availability.
- [x] 3.3 Update active-policy handling in `H/actual_judge_feedback.py`, `H/codex_review_reuse.py`, relevant receipt validators and context helpers to validate historical versus new model/effort identities. Verify genuine medium receipts remain readable but are not reused as low reviews, and mixed-provider prompts retain all required input. Record affected paths and passing checks in `P/provider-migration.md`.
- [x] 3.4 Preserve full-source/hash-bound Coder admission and authoritative usage when direct DeepSeek returns alternate model IDs, invalid JSON, reasoning-only output or length termination. Verify the frozen direct-provider and existing anchor/ownership regression tests pass; no generated patch or protected test is handwritten to repair the game.

## 4. Implement canonical evidence and deterministic reduction

- [x] 4.1 Implement `H/evidence_packet.py` with immutable canonical source manifests, candidate/contract/policy binding and exact current integrated patched-file bodies. Verify frozen manifest fixtures and stale-input rejection pass; document packet fields and mandatory review profiles in `P/context-packets.md`.
- [x] 4.2 Implement conservative required-source closure in `H/evidence_context_guard.py` using existing adapter syntax facilities where available; retain full uncertain partial/reflection/dynamic scopes. Verify cross-owner/helper/contradiction fixtures and complete test-source reviews cannot lose required evidence. Include the guard's explicit limits in `P/context-packets.md`.
- [x] 4.3 Implement exact deterministic packing in `H/context_packing.py`: deduplicate bodies and repeated host metadata/instructions, preserve diagnostics/test multiplicity and source semantics, and put stable prefixes first. Verify token/byte reports label estimates and hash-bound source bytes are unchanged in all fixtures.
- [x] 4.4 Integrate secret and authorship filtering before any selector/Judge dispatch. Verify frozen injection fixtures reject Coder reasons, private reasoning, author identity and unapproved configuration content while retaining required unit ownership.

## 5. Implement cheap selection, expansion and Architect handoff

- [x] 5.1 Implement `H/deepseek_context_selector.py` using separate Flash/low paid-call IDs, exact optional source references, strict output schema and the proposed size/optional-content thresholds. Return `OptimizationResult` with optimized input, structured check results, provenance, metrics and delivery decision on every path. Verify malformed/hallucinated/ambiguous spans and policy-changing text fail closed; complete valid plans hydrate exact canonical bytes through `H/evidence_context_guard.py`.
- [x] 5.2 Implement `H/context_call_accounting.py` and exact-plan caching against the existing ledger without graph units or budget resets. Verify one selector attempt per canonical/policy hash, all pilot/expansion/audit charges, cache breakdowns, unchanged old reservations and stopping on unknown usage with frozen recovery tests.
- [x] 5.3 Implement `H/judge_context_adapter.py` around both test review and defect judgment. Verify bounded context requests, one expansion and canonical fallback preserve native final return schemas, fresh identities and exact evidence; context requests must never become game verdicts or tool access.
- [x] 5.4 Implement `H/architect_finding_index.py` for compact handoffs with exact classification/explanation, every unresolved finding, retry/budget state and original artifact references. Verify frozen handoff fixtures detect omissions, retain uncertainty and hydrate inaccessible references; no extra paid model call for short verdicts.
- [x] 5.5 Add `H/context_cost_report.py` and update `P/context-packets.md` with per-purpose usage, cache/latency/fallback metrics, dated prices and explicit unknown dollar rates. Verify break-even fixtures include selector/expansion overhead, retain all billed input and do not claim that quota-token estimates are cash savings.

## 6. Review implementation and qualify the requested models

- [x] 6.1 Run spec-compliance review against both delta specs and record each requirement's evidence in `P/verification.md`; then perform code-quality review for secret boundaries, historical-policy compatibility and no runtime/Unity leakage. Resolve findings within host ownership and verify the frozen test hashes remain unchanged.
- [x] 6.2 Run full offline `uv run pytest -q` from the isolated checkout and `uv run langgraph dev --allow-blocking`; verify tests pass and the unchanged graph compiles/is listed. Record fresh outputs in `P/verification.md`, stop only the task-owned development server, and confirm `src/` plus pinned overlay diffs are empty.
- [x] 6.3 Verify the local `ai.local.toml` key without displaying its value, check official direct endpoint/model mapping and exact GPT-6.1 Sol low availability, and record nonsecret capabilities in `P/pilot-report.md`. Missing keys or unavailable low effort are explicit blockers, never substitutions.
- [x] 6.4 Reserve a bounded pilot sub-envelope of at most 10,000,000 additional input / 512,000 output within the existing aggregate budget; record it in `P/pilot-report.md` and trusted accounting. Verify all conservative call reservations fit and preserve prior usage; no dispatch if required evidence cannot fit this envelope.
- [x] 6.5 Run one bounded direct Coder protocol fixture and four candidate-bound canonical/optimized paired review classes with GPT-6.1 Sol low, at most four selectors and eight initial Judge reviews. Verify genuine usage/model/effort receipts and adjudicated expected findings; count all failed/expanded calls in the envelope and never apply pilot source to the game.
- [x] 6.6 Publish `P/pilot-report.md` with mandatory-item coverage, correctness/disagreements, median and per-class Judge-input reductions, selector overhead and actual/estimated net cost. Verify zero omissions/wrong adjudicated routing, the 40% median goal and 20% per-class gate, and 10% net-money saving where prices are known. Ineligible classes retain canonical/deterministic input; failed low-Judge qualification blocks migration and requires user resolution.

## 7. Complete backend activation before deferred lobby work

- [x] 7.1 Add `H/mixed_backend_recovery.py` with the exact current operational-stop proof, complete reservation registration and immutable role/context grant. Verify interruption and stale-identity tests pass, then compare candidate, contract, every historical charge/reservation, freeze and overlay hashes with task 1 before public native activation. Preserve previous effects and grants byte for byte.
- [x] 7.2 Activate the verified direct Coder/low Judge composition and qualified context classes through trusted host configuration; invoke supported native recovery for `monopoly-game-lobby` using fresh IDs. Verify the first completed actual receipts identify DeepSeek Flash low and GPT-6.1 Sol low, unchanged aggregate ceilings and no replayed coding/verification effects.
- [x] 7.3 Install the persistent first-ten-review observer and perform one budget-covered canonical/low shadow audit against an exact archived live packet; write the actual observed count and audit outcomes to `P/pilot-report.md`. Verify no mandatory omissions or unexplained routing disagreements; disable the affected selection class without changing models or counters if a guard fails. Remaining observations continue with the deferred lobby run.
- [x] 7.4 Finish backend-only packing/accounting corrections and fresh current-format qualification under the original persistent sub-envelope. Verify free exact reductions bypass the paid-selection threshold, every old global charge/reservation remains, frozen offline checks pass, and prior-format pilot evidence cannot activate the new formatter. Let the current native invocation settle without starting another lobby contract or editing its frozen tests.
- [x] 7.5 Deliver `P/verification.md` with backend acceptance met/unmet, exact host checkpoints, genuine model/effort receipts, current budgets, usage/reservations, optimization/check metrics and limitations. Record the lobby's actual stopped candidate and deferred conflicts separately; do not claim game acceptance or `awaiting_human_review`.

## Workflow follow-up

- The user deferred lobby frozen-test conflict resolution until this backend implementation is finished. Preserve the conflict report and all old frozen versions. No scope exception was granted; new test authoring or a product contract needs that later decision.
- Continue the existing lobby to `awaiting_human_review` only after resolving its contract conflicts through the authorized workflow. Its remaining first-ten-review observations and exact-candidate human review package stay with that continuation; they are not evidence of backend implementation completion.

- Await the user's revision-specific lobby review; finalization and product task reconciliation remain governed by the existing acceptance rules.
- Promote a generic direct-provider or context capability into framework runtime only through a separate reviewed change, if the rehearsal results justify it.
- Archive or sync this planning change only when requested and after its acceptance requirements are satisfied; no automatic mainline commit, push or merge.
