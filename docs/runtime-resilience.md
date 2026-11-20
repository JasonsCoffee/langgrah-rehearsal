# Framework resilience amendments

The user authorized promoting reusable rehearsal fixes into the framework and
saving them on a feature branch. The lobby run remains paused; no paid model,
Unity operation, runtime migration of that run, merge or push is part of this work.

## Accepted behavior

- Keep configurable stage budgets, optional model caps and authenticated abandoned
  run recovery, including the earlier frozen tests. Preserve uncertain charges.
- Invalid structured worker/judge output ends operationally, with safe diagnostics
  and no unit-attempt charge, automatic request replay or test unfreeze. Valid
  negative reviews retain the judge's actual actionable explanation.
- Author feedback belongs to its author. Persist it across restart; clear it on
  successful review. Baseline setup findings go only to implicated authors.
  Implementation feedback remains separate. Old checkpoints stay loadable; an
  unscoped old author message is never guessed to belong to another unit.
- A host may declare required per-unit context paths and exact UTF-8 hashes.
  Reject absent/changed requirements before any paid call at all five stages.
  Include a contract-bound hash manifest of actual supplied text in each prompt.
  Required context policy is trusted host composition, not model-selected files.
  Natural-language references are not automatically inferred as a complete list.
- A trusted host may reconcile a pending effect through a validating callback.
  Require exact original effect identity and nonempty existing hashed evidence.
  Preserve the pending-intent digest and resolution evidence in one atomic receipt.
  Completed effects are immutable. Missing/changed/conflicting proof stops without
  altering the pending record. This API never calls models, changes budget or
  bypasses normal patch ownership/freeze checks and independent review.
  The host callback must verify paid usage/reservations, exact delegated outputs
  and candidate/source identity; a file hash by itself proves no semantic verdict.

## Deferred proposals

A safe pause/resume protocol needs call-boundary quiescence and explicit durable
resume semantics. Cross-cycle source-review reuse needs a dependency-complete
fingerprint and invalidation rules; owned bytes alone are insufficient. Neither
is implemented or enabled by these amendments. Direct TLS, response formatting,
model-effort settings and Unity overlays stay in transport/target composition.

## Frozen validation

Thirty new offline regression cases failed against the previous runtime after
fixture validation and before implementation. Frozen test SHA256: `c07df69d38199146175074376c7467c5b2ec826a6f1974d9220acf5f9a4bf248`.
Use fake providers and disposable Git fixtures. Required completion checks are
full pytest, graph compilation/listing, diff hygiene and a clean feature commit.
No previous rehearsal run state or credentials may enter that commit.

One additional live-effect race regression was observed failing, then frozen before the shared-lock fix. Its SHA256 is `82c2cae5e8f19bfcb056c318bc9ae5a5e2da6564b00c436ab6c9964de1abbdfd`. All 31 new cases passed in 10.45 seconds before full-suite verification.

A final setup-to-implementation feedback regression was also observed Red before correction. Its frozen SHA256 is `9a77a87b8485d7de1b203799d78866bfb5fb07c311fe107529300df638af7245`. The first full suite passed 569 cases; after that boundary correction the final suite includes 570. Exact final results are recorded below.

Existing checkpoints and paid receipts are preserved. Prompt manifests change new request text, so upgrading a host with pending paid operations requires explicit reconciliation against their original identities; never regenerate a pending prompt under its old call ID. This branch is not activated in the paused lobby host.

## Final validation

- `uv run --no-sync pytest -q --tb=short`, using the existing project environment
  with the isolated worktree source selected: **570 passed**, one existing
  TestResult collection warning, 253.42 seconds. No provider or Unity access.
- All 32 new regression cases were observed Red before their corresponding fixes;
  their three frozen source hashes above remain unchanged.
- `uv run --no-sync langgraph dev --allow-blocking --host 127.0.0.1 --port 2028
  --no-browser` compiled the final source and `/assistants/search` listed
  `unity_coder`. Process-local PYTHONUTF8 was enabled; the server was then stopped.
  No graph run was submitted and no dependencies were changed.
- `git diff --check` passed. The feature commit excludes credentials, target assets,
  rehearsal worktrees and trusted run state. Existing unrelated checkout changes
  are preserved. No mainline commit, merge or push occurred.
- The paused lobby budget, policy, executor, status, candidate selection and service
  checkpoint stayed byte-identical during this amendment. It is not resumed or
  upgraded automatically. No new paid model call was made.

The implemented runtime amendments meet the accepted code-only behaviors above.
Pause/resume and cross-cycle review reuse remain proposals, not delivered runtime
capabilities. Functional lobby acceptance remains outside this code-only change.
