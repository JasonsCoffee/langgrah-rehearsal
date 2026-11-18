# Implementation evidence

## Production-wiring follow-up — 2026-11-18

W1–W3 from verification-review.md are resolved. Eleven new regressions in two
files were observed Red and frozen before their associated fixes; all 71 frozen
hashes match and no earlier frozen test was changed.

- W1: post-stage status retains per-unit counters. The regression observes a failed
  preparation attempt, cancellation and reconnect without losing the count.
- W2: production review emits a candidate-bound ReviewPackage, including scope,
  launch instructions, required interactions, entries, visual references and
  placeholder limits. Visual metadata is validated against reviewed files; stale,
  missing or escaping inputs are rejected. Same-request metadata is immutable.
  Architect observation/reconnect now returns review_package without dispatch.
  Explicitly code-only contracts receive code/spec review guidance, not an invented
  scene. Richer visual guidance remains a typed trusted-host callback.
- W3: confirm_constraints validates exact human approval and evidence provenance,
  persists the immutable entries and serializes with completion. Finalization and
  crash recovery reuse those entries. Tests prove a real metadata commit containing
  one learned statement, no flush for pending/stale/forged input, idempotency,
  changed-entry refusal and recovery of the same commit after ref publication.

Commands and results:

| Command/check | Result |
|---|---|
| `uv run pytest -q tests/test_production_review_delivery.py` before fixes | 10 failed, expected Red; frozen before implementation. |
| New delivery tests plus executor review-resume and terminal-recovery tests | 16 passed, 77.77 seconds. |
| `uv run pytest -q` | 478 passed, one existing collection warning, 193.68 seconds. This run collected before the additional observation regression and its boundary fix. |
| `uv run pytest -q tests/test_review_package_observation.py` before boundary fix | 1 failed, expected missing review_package; frozen before implementation. |
| Observation regression plus architect_boundary, boundary_reconnect and local_invocation suites after boundary fix | 33 passed, 17.46 seconds. Covers the final boundary change and the extra test; 479 distinct tests across full and focused checks. |
| Graph dev server with `--allow-blocking --no-browser --port 2025` | Compiled; assistants/search listed unity_coder and its graph endpoint returned all production nodes; owned server stopped, no listener remained. |
| `pnpm exec openspec validate formalize-unity-feature-delivery` | Exit 0; existing independent-judge requirement-length advisory remains. |

Review order: spec compliance, then implementation/recovery/host-boundary checks.
Current reviewed-files.json records 127 files against the published implementation
base plus these uncommitted fixes. No new dependencies, Unity operations, paid
calls, Monopoly edits/tests, commit, push, synchronization or archive occurred.
Prior real-Unity acceptance limits still apply: this follow-up proves the new
wiring with offline disposable Git fixtures, not fresh live human acceptance.

## Task 12.7 final acceptance scope — 2026-11-18

This section supersedes historical readiness statements below. It records the
framework implementation and authorized isolated demonstrations, not delivery of
a Monopoly feature. Fresh command results are recorded below. The phase matrix deliberately distinguishes implemented behavior,
prior live demonstrations, and unverified combined production acceptance.

### Fresh final commands and outcomes

Commands ran from the framework repository with UV_CACHE_DIR=.uv-cache and
PYTHONUTF8=1 for Python commands. No Unity host command was issued.

| Check | Observed outcome |
|---|---|
| `uv run pytest -q` | Exit 0; **468 passed**, one existing TestResult collection warning, **144.12 seconds**. |
| `uv run langgraph dev --allow-blocking --no-browser --port 2025` | Application started and production graph compiled. |
| Local POST `/assistants/search`, body `{}` | HTTP success; graph_id and name both unity_coder. |
| Local GET `/assistants/unity_coder/graph` | HTTP success; start/reconnect/prepare/red/code/verify/refactor/final_verify/review/finalize/repair/rework/end nodes present. |
| Ctrl-C to owned server; listener check | Owned process exited 1 due to intentional interruption; no listener remained on port 2025. |
| Frozen/reviewed manifest SHA256 audit | All 69 frozen entries and all 125 reviewed implementation entries match. |
| `pnpm exec openspec validate formalize-unity-feature-delivery` | Exit 0, valid; advisory warning that the independent-judge requirement exceeds 500 characters. |
| Same validation with `--strict` | Exit 1 solely for that length warning. This is not reported as strict validation success; no frozen requirement was rewritten to suppress it. |

All task 12.7 checks and the final scope record are complete. The tracked change
is 61/61; no spec synchronization, archive, commit or push was performed.

### Reviewed implementation identity

Git base: `4c6ab4e8f51a9e700a785c998d5be6bc8852f720`. The implementation is an
uncommitted working tree; that commit alone does not identify it.
All 125 entries in reviewed-files.json match the reviewed bytes; its SHA256 is
`b1ffdcb49e950cca567cbcef9ec6a57f867fa1e4088ad1abe818a4d51dfe81df`.
All 69 frozen entries match; frozen-tests.json SHA256 is
`ba3aecf3e6811bf4da98425ed6eddbf05ee51d38852c5197b946f7a9ecc1a20f`.
No runtime source, test, dependency, or Unity helper changed in task 12.7.
The in-session compliance/code review is recorded in compliance-review.md;
R1–R10 are resolved. This is not an independent external audit.

### Phase criteria and evidence

| Phase / extension | Criterion disposition | Evidence and limits |
|---|---|---|
| 0: packaging and graph foundation | Met historically; current graph smoke freshly verified. | Initial uv sync succeeded, Python 3.12 pinned, empty skeleton collection exited 5 as expected. The historical zero-test criterion is not rerun against the implemented suite. Current production graph imports and lists all stages. |
| 1: contract/ownership | Met offline. | Contract/target-profile tests reject collisions, empty owns, protected specs, invalid DAGs and migrations; adapter-selected case rules, lineage, hashes and scope checks pass. |
| 2: adapter/conformance | Met offline. | Adapter tests report file/symbol signature failures, preserve generated exemptions and protected metadata, and use tree-sitter without an editor. Core remains stack-independent. |
| 3: test-first dispatch/freeze | Met offline; isolated live TDD demonstrated previously. | TDD/integrity/dispatch and production tests enforce independent preparation, global freeze, baseline Red, Green, Refactor and no-change rationale. Frozen tests reject implementation writes. |
| 4: blocking verification | Met offline; live Bridge boundary demonstrated previously. | Ladder stops at each failing rung, preserves unit/shared attribution, rejects stale/empty/skipped evidence, and requires full selected acceptance before review. Production streaming proves focused verification overlaps independent coding without concurrent mutation. |
| 5: bounded repair/dossiers | Met offline. | Loop/dossier and production regressions cover immediate STALLED escalation, first-regression owned rollback, second regression/exhaustion escalation and mixed per-unit classifications. No budget reset during repair. |
| 6: real stack/model execution | Isolated coding and presentation milestones met; combined live accepted production delivery remains unverified. | Complete pinned host, Bridge reload/callbacks, new-file negative compile, two external coding worktrees, five-test Red/Green/Refactor/shared routing, distinct real coder/judge, and exported graph reaching awaiting_human_review are recorded. Separately, the visual fixture and later lake artwork received exact-candidate human acceptance. Those approvals do not approve the model-driven candidate. |
| 7: branches/governor/constraints | Implementation criteria met offline with real disposable Git; accepted constraint flush on the live model-driven candidate remains unverified. | Budget/governor tests prove reservations, preserved unknown usage, stop dispatch, abandon/dossier and retained branches. Completion tests prove exact authenticated parent, managed-block provenance/deduplication/40-entry archive, unrelated-content preservation and crash recovery. No live accepted pass or constraint flush is inferred from automated Green. |
| External workspaces/materialization | Met offline; isolated host evidence recorded. | Workspaces stay outside Unity import, mediated tools enforce ownership, one candidate is materialized, dependency/settings drift rejected, user starting work preserved. Unrestricted process agents are unsupported. |
| Progress/cancellation/recovery | Met offline in production paths. | Frozen production observation, streaming and effect-recovery tests cover heartbeats/attempts/active candidate, shared dependency groups, cancellation, commit/receipt interruption, rollback and completion. Unknown paid calls and ambiguous dirty state stop for trusted reconciliation; no blind replay. |
| Presentation/review/artist contract | Met for the authorized synthetic demo. | Scene/prefab/shell/binding preparation, protected metadata, explicit launch/interactions, human repair/rework, incompatible art rejection, compatible lake replacement and renewed approval are recorded. Existing game PSD/map workflows were not exercised by this synthetic brief. |
| Delegated OpenSpec boundary | Met at the local host-composed API. | Context export, task relationships, reconnect, structured results, consecutive contract revisions and same-run budget continuity pass. Architect retains planning authority. CLI export/status and invoke_local are implemented; arbitrary remote execution is outside scope. |

### Live evidence boundaries

- `live-evidence/production-graph-resumed/`: candidate
  `fb0ae7307066d1bec4152c45e0b13b3153aca8ab` reached awaiting_human_review.
  This model-driven run has no recorded human acceptance or live metadata-only
  completion. Its budget and state were not changed for final verification.
- `live-evidence/visual-review/` and `art-replacement/lake/`: separate operator
  rehearsals, with explicit approval of the final lake candidate
  `92e7ca321be8462a445cf1d7acc0e5f566509cadd41ea4ca6a04cce30381dba3`.
  Approval cannot transfer across candidates or runs.
- `live-evidence/callback-validation/`: the task 12.6 helper compiled and six
  isolated demo tests passed. Frozen probes verified behavioral assertion versus
  nonbehavioral setup and suite-only teardown. Temporary probe source was removed;
  3,595 original game files and all 14 host repositories were unchanged.
- Live production crash/cancellation, ownership migration and accepted constraint
  flush have offline coverage but were not newly rehearsed against Unity and
  paid models after R7–R10. No fresh Unity test or paid call was made in 12.7.
- Full original Monopoly suite acceptance is not claimed. Historical failures
  remain deferred by user instruction; its code and existing tests are untouched.
  The isolated five/six-test selections are full acceptance only for their own
  fixtures, never substitutes for a passing whole-game suite.
- Automated PlayMode policy, production final art, other stack adapters, remote
  workers and automatic mainline merge/push remain excluded future work.

Task 12.7 completes the final verification/reporting checklist without converting
these explicitly unverified live criteria into accepted delivery. Phase 6 as a
combined human-accepted production run is not declared complete. Phase 7 has
verified implementation behavior, not a fabricated live accepted result.

## 2026-11-18: task 12.6 follow-up signed off

R7–R10 resolved and the updated Unity callback validated. Progress is 60/61;
task 12.7 remains separate. compliance-review.md contains the updated requirement
matrix and review scope; reviewed-files.json identifies current reviewed bytes.

- Red/freeze/Green: observation_cancel (3 failures), effect_recovery (2 failures),
  streaming (2 failures), terminal_recovery (2 failures), effect_edges (2 failures,
  1 already-passing conservative unknown-call check). These five new files contain
  twelve offline regressions. Existing frozen tests were unchanged.
- `uv run pytest -q`: exit 0, **468 passed**, one existing TestResult collection
  warning, **145.26 seconds**. All **69** frozen file hashes match, including the
  separately frozen CallbackProbeTests.cs live diagnostics.
- `uv run langgraph dev --allow-blocking --no-browser --port 2025` with
  PYTHONUTF8=1: graph compiled; POST /assistants/search listed unity_coder. The
  owned server was interrupted; no listening port remained.
- `uv run python examples/visual_baseline/callback_validation.py` with UNITY_HOST
  selecting the dedicated host: updated helper compiled successfully, six demo
  tests passed; assertion probe produced one behavioral failure, setup probe
  produced one nonbehavioral failure, suite-teardown probe produced a passing
  leaf plus nonbehavioral suite error. The latter two were rejected by the TDD
  evidence validator. The first setup run exposed Unity runner site loss; source
  inspection and the frozen probe drove the prefix-handling fix before rerun.
- Receipts: live-evidence/callback-validation/{compile,demo,assertion,setup,
  suite-teardown,integrity,repository-audit}.json. Temporary diagnostics removed.
  Accepted presentation unchanged; 3,595 original files unchanged; 14 repositories
  tracked-clean. Existing game tests were neither selected nor edited.
- Recovery automatically reuses proven completed effects; unknown paid results,
  ambiguous uncommitted mutation or foreign state stop for trusted reconciliation.
  No paid calls, reset budgets, new dependencies, commits or pushes.


## 2026-11-18: task 12.6 compliance/code review checkpoint

Review disposition: **not signed off**. compliance-review.md maps all four delta
specs to implementation/evidence and records six fixed findings plus four open
production integration findings. reviewed-files.json identifies the uncommitted
source/test/editor bytes reviewed; a base Git commit alone does not identify this
rebuilt implementation. Task 12.6 remains unchecked; progress stays 59/61.

New regressions observed Red and were frozen before the associated fixes:
test_review_compliance.py (4 failures), test_review_path_aliases.py (2 failures),
test_review_test_evidence.py (7 failures), test_review_preparation_routing.py
(2 failures), and test_review_shared_routing.py (2 failures). All subsequently
passed. Existing tests were not rewritten to fit changed code.

Final regression command `uv run pytest -q`: exit 0, **456 passed**, one existing
TestResult collection warning, 77.38 seconds. All **63** frozen file hashes match.
`uv run langgraph dev --allow-blocking --no-browser --port 2025` started and
compiled; POST /assistants/search listed unity_coder. The owned process was
interrupted and no listener remained. UnityAdapter.parse_check found zero syntax
violations across all four unity/Editor/*.cs files. This is not C# compilation:
the updated verifier callback still needs isolated live validation before relying
on its new failure-detail protocol. Historical callback receipts are retained;
failed callbacks without classification now fail closed instead of assuming Red.

No Unity commands, existing game tests, host mutations, paid model calls, new
dependencies, commits or pushes occurred. Only read-only installed test-runner
interface inspection supplemented the offline review. The accepted lake candidate
and its approval remain unchanged. Final whole-system task 12.7 is not claimed;
production scheduling, in-flight observability, cancellation and effect recovery
must first resolve findings R7–R10.

## 2026-11-18: task 12.5 isolated artist replacement rehearsal

Two separate synthetic artist deliveries exercised the existing replacement
policy outside a coding cycle. A 320x320 opaque PNG failed the 768x480 dimension
requirement and was rejected before import; the approved baseline remained
byte-identical. The compatible dawn landscape passed dimensions, opacity and
existing import-setting checks. Only its PNG bytes changed among the 13 protected
presentation files. Metadata, canonical GUID, sprite local ID, prefab reference,
scene, component shell, bindings and layout remained unchanged. Both deliveries
have retained host receipts; portable evidence is under live-evidence/art-replacement/.

The reviewer answered "Request visual changes" for candidate 61b193bac7fe, then
specified "there should be a lake". That candidate is not accepted. A separate
lake revision retains the rejected artwork and its evidence, adds a lake and
sunlight reflection, and again preserves references. Lake candidate:
`92e7ca321be8462a445cf1d7acc0e5f566509cadd41ea4ca6a04cce30381dba3`.
Presentation identity:
`f4cc3ef153d1451bdbd9d66ecf65fc592d9655b4ecc2c3ae0278100ef3d7e465`.
The user explicitly answered "Approve lake revision and interactions" for this
candidate. The operator rechecked current candidate bytes, passing evidence and
all protected manifest files, then applied the replacement policy with that fresh
approval. Authoritative acceptance is lake/acceptance.json and the exact reply is
lake/human-review.json. Earlier pending records remain preparation history.
Task 12.5 is complete; progress is 59/61.

Each compatible candidate compiled and passed all six isolated EditMode tests,
with no failed, skipped or inconclusive test and no operational error. Existing
Monopoly tests were not selected. The core policy rejected missing separate-change,
compatibility, reference-preservation and human-review evidence. Old manifests
rejected replacement bytes; new manifests passed Unity import/binding validation
and distributed immutable copies outside Unity imports. This is a component
rehearsal with synthetic art and fixture contract/profile labels, not a production
coding/model run. No coding budget was reset or spent. The user-reviewed original
v2 snapshot remains intact.

Offline suite: 439 passed, one existing collection warning (74.40 seconds).
All 58 frozen file hashes match. The development graph compiled and the local
assistants API listed unity_coder; the owned server was stopped. All 14 dedicated
host repositories were tracked-clean, and all 3595 original game file hashes
matched after the lake replacement. No new dependencies, frozen-test changes,
mainline commits or pushes. Rehearsal steps and scope are documented in
examples/visual_baseline/art-replacement.md. Final whole-system
review (12.6–12.7) is not claimed.

## 2026-11-18: task 12.4 accepted isolated review rehearsal

The user explicitly approved the existing visual baseline, selected "Change the
primary button to warm coral", and then answered "Approve v2 and its interactions"
to the question naming candidate 4c66aaf33a38. The trusted operator imported those
actual decisions as receipts. ReviewGate records the human as chat-user, the
exact request/candidate, decision, version, time and evidence refs. Credentials
are transient and not persisted. No model or agent self-approval is substituted.

This is a live component rehearsal of ReviewGate, RunLifecycle and BudgetLedger
with actual Unity compile/EditMode evidence. It is not a new exported-graph/model
run or production authentication deployment. Fixture contract identifiers are
explicit rehearsal labels, not full production contract exports. Existing frozen
executor/cycle tests exercise the production transition paths in the offline suite.

The exact mint baseline first passed its three original demo checks and recorded
acceptance. A supervised diagnostic changed only the shell's ready-text assignment;
it was not a coding-unit write inside a frozen cycle. New EditMode interaction
tests initially exposed a harness defect: runtime-only listeners do not fire in
EditMode. Before freezing, the tests enabled EditorAndRuntime only on temporary
instances. No authored prefab or existing frozen test was changed. Intended Red
then showed four passes and one primary-button failure; the tests were frozen.

The gate rejected old-approval finalization of changed source (Completion changes
reviewed content) and refused to offer a failing candidate. Exact source restoration
yielded five passes in version 1; the old request was rejected on fresh review.
This is automatically detected implementation repair, not a fabricated human
rejection. The user's actual color finding recorded decision contract/action
rework. One new coral requirement test was Red with the other five passing, then
frozen. The Architect-only revision checked the original prefab hash, changed its
primary color to #F6A98B, and preserved GUIDs, hierarchy and bindings. The synthetic
brief records the superseding requirement. Original v1 evidence/files are retained.

Final candidate: `4c66aaf33a38893a6488f678be469af8e2439950cc79cb434611616209bde834`.
V2 presentation identity: `7150c88cae377b3622c22f1eb6e2c05f308de2f4c7dc33be7ef7e413c64b223a`.
Its snapshot includes all demo test sources/metadata as well as the 13 baseline
files. Compilation and all six isolated tests passed with no skips/inconclusive
cases or operational error. V1 approval was rejected for v2. Only after the user's
new reply did accept-v2 recheck current bytes and persist acceptance. No runtime
pass/completion revision, constraint flush, merge or push was manufactured.

Rehearsal commands (via `uv run python examples/visual_baseline/review_rehearsal.py`):
accept-baseline, inject, verify-fault, repair-resume, request-rework, coral-red,
prepare-v2-report, coral-review and accept-v2. UNITY_HOST and VISUAL_REVIEW_ROOT
select host/state; VISUAL_BASELINE_VERSION=2 exports a separate v2 snapshot.
Two post-compile Bridge discovery/connection interruptions were reconciled with
the same request identities. The helper waits on read-only capabilities after
compilation instead of repeatedly refreshing the editor. The same ledger retains
cycles 1 and 2, zero calls/usage and unchanged limits. The earlier production run
and budget were never accessed for mutation.

`uv run pytest -q`: **439 passed**, one existing collection warning, exit 0,
72.27 seconds. All **58** frozen file hashes match. Script py_compile passed.
The original-file audit found **3,595 unchanged** tracked game files and **14
tracked-clean** host repositories; existing Monopoly tests were not executed.
Desktop capture was unavailable for the minimized Unity window, so no new manual
agent screenshot is claimed. Visual acceptance was supplied by the user.

`uv run langgraph dev --allow-blocking --no-browser --port 2025` compiled the
graph; POST /assistants/search listed graph_id/name unity_coder. The owned server
was stopped after the check. OpenSpec apply instructions confirm 58/61 complete
and task 12.4 checked. The authoritative accepted review is v2-acceptance.json;
the earlier export's pending review.json is retained as preparation history.

Task 12.4 criteria are met for the authorized isolated rehearsal: explicit
revision-bound acceptance, detected/repaired interaction, requested presentation
rework, fresh verification/review and stale-approval rejection. Tasks 12.5–12.7
remain open; this does not establish full-game acceptance or final-art replacement.

## 2026-11-18: task 10.3 isolated visual preparation

User explicitly requested a synthetic isolated visual-baseline demonstration and
excluded Monopoly feature work and existing tests. Implemented Architect-side
FrameworkVisualPreparation plus PreparedBaseline export; reused the installed
PsdPrefabLayoutAutomation read-only inspector, Unity prefab/scene/import APIs and
existing game assembly conventions. No PSD or map conversion applies to this
synthetic reference; original game source, layouts, maps, bindings and designs
were preserved. The fixture adds only named FrameworkVisualDemo folders and its
own preparation helper. No dependency additions.

The 11 new offline preparation cases failed against the unimplemented API, then
were frozen and passed. Three new isolated Unity tests were frozen, installed,
observed failing because the scene/prefab/sprite did not exist, then passed after
preparation. Existing Monopoly tests were neither edited nor executed. The first
live export correctly rejected Tuanjie's encoded metadata GUID versus canonical
AssetDatabase identity. A new frozen offline regression reproduced that missing
mapping support; the adapter now requires explicit trusted editor mapping and
GUIDToAssetPath round-trip, retaining protected metadata hashes. The existing
presentation tests were unchanged. Export also uses canonical adapter field
signatures and validates the actual C# shell before distribution.

Commands and observed results:

- `uv run pytest -q tests/test_presentation_preparation.py`: 11 failed before
  implementation; combined presentation suite subsequently 31 passed.
- `uv run pytest -q tests/test_encoded_asset_identity.py`: 1 failed before fix;
  combined presentation/preparation/identity suite subsequently 32 passed.
- `uv run python examples/visual_baseline/live.py red`: 3 executed, 3 failed,
  no operational error, no unrelated game test execution.
- `uv run python examples/visual_baseline/live.py create`: generated scene,
  prefab and imported 768 x 480 opaque Sprite/Single placeholder.
- `uv run python examples/visual_baseline/live.py inspect`: launchable true,
  no missing scripts or unresolved bindings; existing prefab inspector succeeded.
- `uv run python examples/visual_baseline/live.py green`: 3 executed and passed,
  no skipped/inconclusive/failed cases or operational error.
- `uv run python examples/visual_baseline/live.py compile`: passed, no violations
  or operational error. Compilation succeeded with the actual shell/helper installed.
- `uv run python examples/visual_baseline/export.py`: validated and distributed
  13 protected files with identical content/metadata into the external preparation
  worktree. Manifest identity is recorded in live-evidence/visual-baseline/review.json.
- `uv run python examples/visual_baseline/live.py check-originals`: all 3,595
  pre-existing tracked game files unchanged, including original designs and tests.
- Final `uv run pytest -q`: 439 passed, one existing collection warning, exit 0
  (73.00 seconds). All 56 frozen file hashes match.

The external preparation worktree is on codex/visual-baseline-v1, based on pinned
game commit 4bdfa8b. It retains uncommitted demo additions; no mainline commit,
merge or push was made. The review identity is the content-addressed presentation
manifest, not an invented Git candidate commit. The earlier production coding run
and its budget are untouched. No human approval or coding dispatch follows from
this preparation automatically.

Manual agent inspection through the Unity Game view observed the complete portrait
layout, the ready button changing status to READY FOR REVIEW and reset restoring
BASELINE PREVIEW. Screenshots retain both states. This does not constitute human
acceptance or automated PlayMode testing. Returned the editor to Edit Mode with
the review scene open. A shared dynamic font-atlas texture drift was archived in
the host's operational evidence folder and restored to its pinned tracked bytes;
no shared source or setting changes are part of the baseline.

Task 10.3 preparation criteria are met for the authorized isolated fixture.
Actual human review, broken-interaction repair/presentation rework rehearsal,
artist replacement rehearsal, and final compliance review remain outstanding
under tasks 12.4–12.7. This is not full-game acceptance or final-art production.

## 2026-11-18: coder response diagnosis and preserved-budget live resume

The exact failed coder prompt was reconstructed and matched to its recorded SHA.
A bounded diagnostic call returned HTTP 429. A second small request captured the
upstream explanation: Baidu, limit_source upstream_provider_shared_pool. The key's
account had credit. The original two failures had no retained error bodies, so
their exact historical HTTP responses cannot be recovered. This reproduction
establishes the current rate-limit failure and the successful resolution below.

Added optional upstream_provider configuration, pinning only `alibaba` for the
same configured DeepSeek model in the ignored local config. Temperature zero and
the judge's approved policy remain unchanged; automatic fallback remains false.
Explicit endpoint restriction follows the provider `only` option documented by
[OpenRouter](https://openrouter.ai/docs/guides/routing/provider-selection).
ModelCalls binds routing to call identity, persists sanitized HTTP status, retry
hints and limit source, retains partial model content as failure evidence, and
charges valid reported usage even when a response is rejected. No incomplete
response becomes an executable patch and no failed paid call is silently replayed.

`uv run pytest -q tests/test_model_failure_diagnostics.py` initially exited 1
with four failures; the file was frozen before changes. The affected model suite
then passed 24 tests. Final `uv run pytest -q` exited 0 with **427 passed**, one
existing collection warning (72.41 seconds). All **53** frozen file hashes match.
With PYTHONUTF8=1, `uv run langgraph dev --allow-blocking --no-browser --port 2025`
compiled the graph; POST /assistants/search listed unity_coder. The owned server
stopped and no listener remained. No dependency additions or existing test edits.

Before resuming, checked the original result against actual integration HEAD,
clean Git state and all ten frozen fixture hashes. Archived the old service
checkpoint before adding its validated candidate_revision field. The existing
run then resumed its code stage with new operation IDs and the original budget.
Commands used the existing DEMO_ROOT/UNITY_HOST selectors, DEMO_ATTEMPT=live1,
DEMO_RESUME=1 and `uv run python examples/isolated_demo/production_graph.py`.
The process exited 0: step6 verification passed all five tests; step8 final
verification passed all five again; outcome **awaiting_human_review**.

Candidate `fb0ae7307066d1bec4152c45e0b13b3153aca8ab` is retained on the cycle branch.
Both implementation units reached complete; review.json remains pending. No
human approval, accepted constraint flush or completion revision was fabricated.
All original budget limits, cycles and prior call records compare exactly equal
to the pre-resume evidence. Known actual usage totals **2,821 input / 4,845 output**;
uncertain reservations total **10,368 / 12,320**, including diagnostic requests.
Conservative charged totals are **13,189 / 17,165**. They are not actual billing.
The original uncertain calls remain charged; nothing was reset or erased.

Evidence is preserved separately in live-evidence/production-graph-resumed/,
including the final result, pending review, both passing test reports, full budget
and a continuity audit. Prior operational evidence remains unchanged. All 14
dedicated-host repositories are tracked-clean, and frozen fixture hashes match
the candidate and host. The original game and existing failing game tests were
not changed. OpenSpec remains 56/61: real UI/human/artist acceptance and the final
compliance review remain unverified. No framework commit or push was made.

## 2026-11-17: production executor and same-run revisions

Final commands: `uv run pytest -q` exited 0 with **423 passed**, one existing
collection warning (68.26 seconds). All **52** frozen file hashes match. The graph
compile/list check was repeated after the final governor changes and its owned
server stopped. Pinned apply instructions confirm **56/61 tasks complete**:
12.2/12.3 local integration criteria met; 10.3 and 12.4–12.7 remain unmet.

The exported graph now contains reconnect, prepare, red, code, verify, refactor,
final_verify, review, finalize, repair and rework nodes. ProductionExecutor requires
a host-supplied service instance and held run lease, records intent before each
stage, validates durable terminal receipts and reuses completed service receipts.
LocalExecutionServices composes real external Git worktrees, frozen TDD, parallel
coding callbacks, sequential integration/verification, bounded independent test
preparation, per-unit retry judgments, budget/cycle abandonment and exact-candidate
review/completion. ModelCodingWorkers uses the configured independent coder/judge
through the existing durable reservation mechanism. invoke_local connects the
Architect boundary to this graph; planning files are still never executor output.

transition_cycle requires validated consecutive contracts, the same held run lease
and budget, a matching completed rework dossier, and reconciled workers. It archives
old active records, preserves global progress sequence and all usage/lineage, and
recovers an interrupted transition idempotently. Tests reject skipped versions,
foreign budgets, missing dossiers, active workers and stopped budgets. Explicit
operational resume preserves prior completed stages and paid reservations. Pending
external effects without a completed receipt require host reconciliation.

Every new test file was observed RED and hashed before implementation. Missing
module/API failures established the initial boundary; behavioral RED regressions
also reproduced pre-submission Bridge reload failure, incorrect fresh-start routing,
newline-normalized restore snapshots, committed restart drift, missing Refactor
rollback, final-cycle rework instead of abandonment, and the dev-server file-loader
relative-import failure. No previously frozen test was edited.

The real-Git offline paths cover parallel isolated coding, sequential verifier
calls, frozen tests, pending review, same-version human repair, contract dossiers,
accepted metadata-only completion, bounded test-author preparation, model operational
failure, resource abandonment, and retained branches. Human identities and verifier
results in these tests are explicit offline fakes, not live human approval.

Live exported-graph diagnostic: production-graph-live1 used the existing isolated
fixture and configured models on the dedicated host. Independent test review
completed (619 input / 210 output tokens). The first Red request compiled but
could not discover the Bridge before tests. This operational result is retained.
After a frozen pre-submission discovery regression and bounded recovery fix,
the same run resumed without repeating paid preparation. Red executed all five
selected tests and reported five expected failures. The next two parallel coder
calls produced no usable persisted replies. Execution stopped operationally, with
no integration commit beyond the original fixture baseline. Their actual usage is
unknown: reservations remain charged at 6,108 input / 8,192 output tokens, making
conservative run totals 6,727 / 8,402. These totals are not actual provider usage.
The coarse operational receipt does not establish whether the provider failed or
returned incomplete output; do not infer a more specific cause. No paid call was
blindly replayed. Evidence is in live-evidence/production-graph/.

The live fixture is retained at its baseline candidate. There is no exported-graph
live Green, Refactor acceptance or human acceptance claim. Prior component-level
real-model Green evidence remains separate. Existing game test failures remain
deferred. All 14 dedicated-host repositories were checked tracked-clean. No original
interactive project changes, framework commit, push, model change or dependency
addition occurred.

The dev server initially rejected the new graph's relative import because
langgraph.json loads a file entry point. A frozen file-loader regression reproduced
it; the package import fix passed. With PYTHONUTF8=1,
`uv run langgraph dev --allow-blocking --no-browser --port 2025` started and
POST /assistants/search listed unity_coder. Its graph endpoint returned the actual
production nodes above. The owned server was stopped and its listener was absent.
This proves graph loading, not a remotely configured deployment: local invocation
requires trusted host composition; unconfigured serialized invocations fail closed.

Inline self-review found and resolved byte-preservation, restart-candidate identity,
file-loader, Refactor rollback and last-cycle abandonment defects. Full task 12.6
spec/code-quality review is still outstanding. UI baseline work, real human review,
artist replacement rehearsal and final acceptance remain unverified.

## 2026-11-16: design adoption and Phase 0

Tasks 1.1–1.6 reconcile the approved design into authoritative documentation.
Original decisions D-01 through D-18 remain historical; D-19 through D-27 record
superseding rules. Self-review compared the workspace/worker topology and target
profile with design.md. Live Bridge operation and Unity acceptance remain unmet.

Commands run from the repository root:

| Command | Observed result |
|---|---|
| `pnpm exec openspec validate formalize-unity-feature-delivery --strict` | exit 0, valid |
| `uv python list --only-installed` | exit 0, managed CPython 3.12.11 present |
| `uv sync` | exit 0, 96 packages resolved, 93 installed |
| `uv run pytest -q` | native exit 5, zero tests, expected Phase 0 convention |
| `uv run langgraph dev --allow-blocking --no-browser --no-reload` | application started, graph imported |
| local `POST /assistants/search`, body `{"graph_id":"unity_coder"}` | exit 0, listed `unity_coder` |
| Ctrl-C to owned dev-server session | session exited 1 after interruption |

Commands executing Python required the host permission boundary. The default
uv cache and interpreter queries initially failed with access denied; rerunning
with approved execution and `UV_CACHE_DIR=.uv-cache` succeeded. The CLI help
initially failed encoding emoji through Windows GBK; `PYTHONUTF8=1` resolved it.
These failures are environment evidence, not implementation-test Red.

Resolved versions include LangGraph 1.2.22, CLI 0.4.43, API 0.18.1, tree-sitter
0.26.1, C# grammar 0.23.5, and pytest 9.2.0. Setuptools supplies editable package
installation. Provider SDKs are not required for the skeleton. No credentials or
Unity installation were used by the smoke check. Tracing was disabled.

Phase 0 criteria met: reproducible package, Python 3.12 pin, environment template,
retired wireframe, clean empty-suite collection, compiled/listed stub graph.
Phases 1–7 remain incomplete. No new behavioral tests have been frozen yet;
the skeleton does not claim to execute contracts or provide TDD enforcement.

Self-review order: specification compliance, then code quality. The skeleton
returns `stub`, never a passing execution result, and imports no stack tooling.
No target game writes, mainline commits, pushes, or real-model calls occurred.

## Phase 1 contract milestone

Before implementation, `uv run pytest -q tests/test_contracts.py --tb=no` exited
1 with 52 failures and no skips. The loadable API shell returned no contract and
did not reject invalid inputs; there were no collection/import/tooling failures.
An initial symlink test could not create a Windows symlink; before freezing it
was changed to exercise a real Windows junction and reached its rejection
assertion. File hashes were then recorded in frozen-tests.json for the suite and
fixture. Neither file changed during implementation.

After implementation, `uv run pytest -q tests/test_contracts.py --tb=short` and
`uv run pytest -q` both exited 0 with 52 passed. Full-suite duration was 0.37s.
The Phase 1 graph command used the same flags as Phase 0. A PowerShell projection
initially displayed a null graph ID; repeating the request without projection
and asserting list membership confirmed `unity_coder`. Ctrl-C stopped both owned
sessions (exit 1).

Self-review found contradictory historical attribution and retry prose in the
adopted verification document. It now follows D-22/D-25/D-27: shared relationships,
durable reconciliation before retry, and the first target's HTTP Bridge backend.
No settled decision entry or frozen test was changed. Contract validation uses
immutable records and adapter comparison keys; it imports no stack tooling.
The original Phase 1 acceptance criteria are met. Target profile checks and all
later runtime phases remain outstanding; the graph is still the Phase 0 stub.

Target-profile extension: `uv run pytest -q tests/test_target_profiles.py --tb=no`
exited 1 with 23 failures against its loadable API shell. The suite was frozen in
frozen-tests.json before implementing profiles. Then
`uv run pytest -q tests/test_target_profiles.py` exited 0 with 23 passed in 0.17s.
Profiles preserve rule/source hashes and enforce independently supplied mount and
role scopes. Machine locations are resolved separately. Phase 1's extended
criteria are now met; complete host verification remains a later milestone.

## Phase 2 adapter milestone

`uv run pytest -q tests/test_adapters.py --tb=no` exited 1 with 19 failed and
3 passed against structural API shells. Frozen files are tests/test_adapters.py
and tests/fixtures/csharp/View.cs, recorded before implementation. RED cases
covered parser rejection, signatures/bindings, generated paths, and case policy.
`uv run pytest -q tests/test_adapters.py --tb=short` then exited 0 with 22 passed
in 0.04s. No Unity or compiler was used; the installed grammar was inspected
directly. Self-review confirmed core protocols/evidence have no stack imports,
generated source still undergoes conformance, and unconfigured runtime methods
report operational failure. No frozen test edits were needed.

Fresh `uv run pytest -q` exited 0 with 97 passed in 0.45s. The required Phase 2
dev-server command loaded the graph; local assistant search asserted
`unity_coder` membership. Ctrl-C stopped the owned server (exit 1). Phase 2
criteria are met; runtime editor/model transport is explicitly still absent.

## Phase 3 TDD and dispatch milestone

`uv run pytest -q tests/test_tdd.py tests/test_dispatch.py --tb=no` exited 1
with 25 failures against loadable API shells. Those two files were frozen before
implementation. The same suite with `--tb=short` then exited 0 with 25 passed.
It includes a barrier-based fake-agent test proving two implementation calls
overlap after freeze, plus rejection of patches to frozen tests/configuration.

Self-review identified missing protection between baseline recording and freeze,
missing on-disk Green restoration, and specification drift before dispatch.
New tests/test_tdd_integrity.py reproduced all three with exit 1 / 3 failed;
that new suite was frozen before fixes. No earlier frozen file changed.
`uv run pytest -q tests/test_tdd.py tests/test_dispatch.py tests/test_tdd_integrity.py`
then exited 0 with 28 passed in 0.38s. Failed Refactor restores only owned files.
Crash-safe restoration remains explicitly assigned to Phase 8 journaling.

## Phase 4 verification and shared failures

- `uv run pytest -q tests/test_verification.py --tb=no`: exit 1, 18 failures
  against the ladder API shell; suite frozen before implementation.
- `uv run pytest -q tests/test_verification.py --tb=short`: exit 0, 18 passed.
- `uv run pytest -q tests/test_integration_failures.py --tb=no`: exit 1,
  10 failures; suite frozen before implementation.
- `uv run pytest -q tests/test_integration_failures.py --tb=short`: exit 0,
  10 passed, including mixed per-unit decisions and idempotent shared-round charges.
- Review found a UTF-8 assumption in core. New test_verification_binary.py failed
  as intended (exit 1 / 1 failed), was frozen, then passed after byte interpretation
  moved behind the adapter boundary.
- Fresh `uv run pytest -q`: exit 0, 154 passed in 1.04s.
- Fresh `uv run langgraph dev --allow-blocking --no-browser --no-reload` started;
  local assistant search asserted `unity_coder` listing; Ctrl-C stopped the owned
  server (exit 1). This also supplies the Phase 3 graph smoke check.

Phase 3/4 component criteria are met. The dev graph is still the skeleton, so
these results do not claim complete pipeline wiring or real worker execution.
Specification review preceded code-quality review. No frozen tests were edited;
review regressions were separate newly authored/frozen files.

## Phase 5 retry and dossier milestone

`uv run pytest -q tests/test_loop_control.py tests/test_dossiers.py --tb=no`
exited 1 with 22 failed / 4 passed against API shells. Both suites were frozen
before implementation. The same command with `--tb=short` then exited 0 with
26 passed in 0.13s. Tests cover normalized comparable trends, immediate STALLED,
first/second regression across stages, failed exhaustion, successful last attempt,
expected Red, mixed dossiers, and restoration/invalidation without peer rewrites.
Self-review reused the atomic storage helper in TDD restoration and restricted
retry snapshots to implementation-role ownership. Durable transaction recovery
remains a separate milestone; no end-to-end runtime success is claimed.

Fresh full-suite check: `uv run pytest -q` exited 0, 180 passed in 1.30s. The
Phase 5 graph startup command succeeded; local assistant search asserted the
graph listing; Ctrl-C stopped the owned server (exit 1). Phase 5 component
acceptance is met. Integration into a complete executor is still outstanding.

## Workspace isolation and recovery checkpoint

`uv run pytest -q tests/test_workspaces.py --tb=no` exited 1 with 13 failed.
Before freezing, fixtures were completed with actual nested repositories and all
exported input files. The same 13 cases failed against the workspace API shell.
The suite was frozen, then `uv run pytest -q tests/test_workspaces.py --tb=short`
exited 0 with 13 passed in 7.00s. All commits were in disposable fixture/unit/cycle
branches; no framework or target repository commits occurred. The supported
coding backend exposes mediated file tools, not arbitrary processes or shell.

`uv run pytest -q tests/test_recovery.py tests/test_progress.py --tb=no` exited
1 with 12 failed against API shells. Both files were frozen before implementation.
Initial implementation yielded 10 passed / 2 failed: Windows transient rename
errors affected a journal write and concurrent status publication. A bounded
writer retry resolved that failure mode; the next run had 11 passed / 1 failed.
The remaining failure is reader-side PermissionError in the frozen atomic-read
test, not malformed JSON. A separate ReplaceFileW experiment also reproduced it.
See test-revision-proposal.md for concrete observations and the proposed change.

Fresh `uv run pytest -q --tb=short`: exit 1, 204 passed / 1 failed in 8.29s.
`pnpm exec openspec validate formalize-unity-feature-delivery --strict`: exit 0.
All frozen file hashes match frozen-tests.json. `git diff --check` exited 0.
Task 8.4 is not complete; no recovery-phase completion or end-to-end readiness is
claimed. Later tasks remain unchecked. The user must resolve the frozen-test
revision before implementation resumes under the apply workflow.

## Approved progress-test revision 2

The user explicitly approved bounded Windows read retries on 2026-11-16.
The original test and manifest are preserved in test-history/. Original SHA-256:
8d038712b1f148f7db623d4faf3c5a6b38ef4863e0a917d06a13692ca74a0901.
Only tests/test_progress.py was revised, then frozen again. Added explicit checks
for transient recovery, partial JSON rejection, persistent denial, and other I/O
errors. No production behavior was weakened to satisfy the test.

`uv run pytest -q tests/test_workspaces.py tests/test_recovery.py tests/test_progress.py`
exited 0: 29 passed in 7.44s. This resolves the previous test blocker. Self-review
confirmed error handling remains bounded and user work remains untouched by
managed-workspace failures/cancellation. Tasks 8.4 and 8.5 component checks pass;
complete executor wiring remains outstanding.

## Candidate materialization (task 8.6)

Authored tests/test_candidate_materialization.py against an inert boundary:
`uv run pytest -q tests/test_candidate_materialization.py` exited 1, 16 failures
for missing synchronization and missing rejection behavior. Froze before building.
First implementation passed all 16. Inline spec/quality review found aliasing of
the mount and case-sensitive operational-root protection. New regression file
 tests/test_materialization_integrity.py reproduced 2 failures / 1 pass, exit 1;
froze before fixes. It also injects a disk failure and checks fail-closed restart.

Fresh `uv run pytest -q`: exit 0, 228 passed in 8.49s. All checks use fake hosts;
no target project was modified. Verified metadata preservation, stale managed
removal, exact one assembly mount, dependency/shared-host drift, source identity,
new-meta reconciliation, junction rejection, and interrupted-install rejection.
Graph wiring, live import, and host provisioning remain pending. No complete
Phase 6 or end-to-end executor acceptance is claimed.

## Presentation and review prerequisites (tasks 9.1-9.5)

Authored/froze tests/test_presentation.py after 20 intended RED failures against
an inert boundary (exit 1), then implemented the generic immutable manifest and
Unity structural/import-report validation. GREEN: 20 passed, exit 0.
Authored/froze tests/test_human_review.py after 18 intended RED failures (exit 1),
then implemented trusted-human authentication, exact-request review persistence,
repair/rework routing, renewed review, and metadata-only completion checks.
Fresh `uv run pytest -q tests/test_presentation.py tests/test_human_review.py`:
exit 0, 38 passed in 0.42s. One harmless pytest collection warning concerns the
imported TestResult dataclass, not an unexecuted test function.

Inline specification review: frozen file bytes include metadata and design
references; declared runtime actions are separate from authored mutations;
reused entries and full artist delivery requirements are explicit. Adapter
reports cannot substitute for actual live editor proof. Review self-approval is
excluded by the trusted authentication boundary, which must remain outside model
tools. Inline quality review confirmed restart persistence and stale identity
rejection. Later constraint writer and executor wiring remain required; this
checkpoint claims offline prerequisites only, not complete runtime integration.

## Bridge transport and target preparation (tasks 10.1, 10.2, 10.8)

14 offline Bridge tests failed against the inert API (exit 1), then were frozen.
Implemented bounded local-port discovery, exact project identity checks,
request-specific durable submission intent, callback-only completion, nested error
handling, lost task-ID reconciliation, timeout retention, and typed evidence.
`uv run pytest -q tests/test_unity_transport.py`: exit 0, 14 passed in 0.14s.
The replaced game-local helper uses installed IUnityOpCommand and TestRunnerApi
interfaces, compilation callbacks and RunFinished, preserving request identities.
Its structural parse returned no violations, exit 0. No real C# compilation or
editor execution has occurred; these remain live Phase 6 criteria.

Read-only source inspection recorded 53 portable provenance hashes, actual
assembly/loader/resource identities, engine/package versions and existing game
OpenSpec navigation. Original design and target project files were not changed.
The dedicated UNITY_HOST and GAME_ROOT deployment selectors are not configured.
Task 10.9 needs a designated disposable complete host, pinned nested repositories,
package access, and installation location before live task 10.10 can run.

Fresh full suite: `uv run pytest -q`, exit 0, 280 passed in 8.93s (one imported
TestResult collection warning). Graph startup initially failed because this shell
omitted PYTHONUTF8=1 and dependency OpenAPI loading used GBK. Repeating with
PYTHONUTF8=1 started successfully; POST /assistants/search listed unity_coder.
Stopped the owned server with Ctrl-C (expected exit 1). The exported graph remains
a skeleton: this proves registration only, not complete execution wiring.

## Dedicated host repositories provisioned

User authorized external host and dfw-hecan-20261026 for all repositories, with
mandatory stop on missing branch. Remote preflight found the branch on all 14.
Cloned uengine and 13 nested modules, shallow/single-branch, without executing
toUEngine.py's fallback or copying original working changes. Git tracked diffs
are clean throughout, and nested repositories have no untracked files. Windows
long-path checkout failure in tkmatchwidget was repaired with local core.longpaths
and restoration of its fresh checkout/index from HEAD. No commits or pushes.

provisioned-host.json records exact commits and host manifest/version hashes.
Unity opens at <dedicated-host>/uframework; game remains its independent repository.
The branch does not track Packages/packages-lock.json. Package resolution, helper
installation, actual editor import, and live testing remain pending. Task 10.9 is
not complete until these remaining provisioning criteria are satisfied.

## Live dedicated-host readiness, 2026-11-16

The user explicitly authorized editor launch, package resolution, verifier
installation and live tests. An existing Hub-launched editor already owned the
dedicated project; the extra launch exited and the existing instance was used.
Tuanjie 1.9.2 / 2022.3.62t10, exact project identity verified on port 49166.
Packages resolved and packages-lock.json exists. Installed the helper in the game
Editor/Script/FrameworkVerification directory with a dedicated Editor-only asmdef.
Initial missing Newtonsoft reference was corrected by referencing the project's
existing jj.Json.Runtime. No shared package or shared source was edited.

Durable live-evidence/compile.json: compilation passed with no violations.
Domain reload recovered; FrameworkVerify registered among 42 commands.
live-evidence/smoke.json: one existing EditMode test passed.
live-evidence/match_flow.json: all five MonopolyMatchFlowTests passed, zero
failures/skips/inconclusive. These are labeled host-readiness requests, not a
feature contract or full game suite; the candidate field is the base game commit,
with the installed helper as an uncommitted preparation overlay. Do not reuse
these results as exact frozen feature-candidate acceptance.

Import initially rewrote eight shared tkgamewidget material files. Restored only
those changes from the pinned HEAD; refresh and the subsequent five-test run left
those shared files clean. No user source-project content was changed.

Live compatibility finding: health GET / returns commands=[] because its scene
query can throw before command enumeration on the HTTP thread. ReadConsole invokes
the main-thread registry and confirms FrameworkVerify. Live requests used that
confirmed command directly. The Python BridgeTransport currently requires the
health command list, so its live discovery needs an offline regression and fix.
Do not claim transport end-to-end acceptance yet. Tasks 10.9/10.10 remain open
pending complete provisioning fingerprints and transport reconciliation; new-file
negative compilation inclusion, full-suite and multi-unit demos remain pending.

## Bridge discovery fix and full game suite

Added tests/test_bridge_discovery.py; initial run exited 1 with 1 failed / 1
passed, then froze its SHA-256 before implementation. Added read-only
FrameworkVerifyCapabilities in the game-local helper. Discovery verifies exact
health project identity, main-thread project_info, and protocol/command/modes
before submitting verification. No shared Bridge package edits. Frozen missing
and wrong-project tooling tests remain unchanged. Targeted suite: 16 passed.
Fresh offline suite: 282 passed, one existing collection warning, exit 0.

Installed the updated helper and refreshed the dedicated editor. Ran all 596
previously discovered jj.Monopoly.Tests namespace tests through BridgeTransport,
not manual HTTP bypass. Full result: live-evidence/full-game-suite.json.
596 executed, 570 passed, 26 failed, 0 skipped, 0 inconclusive; no operational
error. Failures group into MonopolyLocalRescueTests (5), MonopolyMonoLobbyTests
(18), MonopolyPawnMotionTests (3). These are baseline game failures before any
multi-unit implementation changes; root causes have not yet been established.
No tracked nested-repository drift was found after the run. The existing full
readiness request is not a feature contract or integrated multi-unit candidate.

Multi-unit live acceptance remains blocked by the non-green game baseline and
must not be marked complete or narrowed silently to a passing subset. No game
behavior or frozen tests were modified to hide failures. Need guidance whether
to investigate baseline game failures first or separately authorize an isolated
multi-unit diagnostic demonstration that cannot claim full-game acceptance.

## Authorized isolated demonstration and governor progress (2026-11-17)

The user explicitly selected the isolated multi-unit demonstration first and
deferred the existing game failures. This supersedes the preceding scope question.
Task 10.5 is complete for that diagnostic scope; full-game acceptance remains
unmet. The full diagnostic selection consists of all five FrameworkDemo tests.
Callbacks are deterministic fixtures, not model calls or an independent judge.

Commands: `uv run python examples/isolated_demo/run.py prepare` and
`uv run python examples/isolated_demo/run.py demonstrate`, using external
DEMO_ROOT/UNITY_HOST selectors and attempt identifiers. The completed attempt is
7, exit 0. Evidence is retained in `live-evidence/isolated-demo/`:

- `red-corrected.json`: five discovered/selected behavioral failures after
  successful compilation. Initial assembly-reference configuration was corrected
  before freezing; compilation errors were never counted as behavioral Red.
- `parallel-coding.json`: overlapping A/B callback intervals in external Git
  worktrees. `ownership-rejections.json`: A cannot edit the frozen test or B's file.
- `partial-shared.json`: one expected failure after integrating A alone.
  `shared-attribution.json` names both A and B and test author T.
- `green.json` and `refactor-confirmed.json`: five selected/executed/passed, zero
  failed/skipped/inconclusive. Refactor explicitly chose no change because each
  implementation is one pure expression. Each gate ran sequentially through the
  exact-project BridgeTransport and durable callbacks.
- `freeze.json` and `summary.json`: frozen test/configuration/metadata bytes match
  in both unit worktrees, integration and the host. Both TDD units are complete.
  The integration commit and candidate hash are recorded; human acceptance is false.

Earlier attempts exposed operational and integrity defects rather than passing:
reload could interrupt HTTP, the refresh task could outlive reload, and Windows
Git newline conversion changed frozen bytes. Two frozen reload regressions failed
before the bounded transport fix; one frozen checkout regression failed before
command-local autocrlf/eol overrides. The disposable baseline's CRLF assembly
definition was recommitted with its original frozen bytes intact; no test bytes
or expected hashes were revised. The harness now checks all frozen bytes before
dispatch. Readiness polling tolerates transient truncated JSON within its bound;
actual verification still requires provenance-matching callback evidence.

Continued Phase 7 with `core/budget.py`: ten frozen tests observed RED before
implementation and now pass. Reservations are atomic across parallel dispatch,
unknown usage survives restart, actual usage is reconciled idempotently, overruns
stop new reservations, and contract cycles/growth/lineages cannot reset usage.
Branch abandonment, constraint flush and executor wiring are still outstanding;
tasks 11.1/11.2 are deliberately not marked complete.

Fresh `uv run pytest -q`: 295 passed, one existing TestResult collection warning,
exit 0. `uv run langgraph dev --allow-blocking --no-browser --port 2025` started;
POST `/assistants/search` listed unity_coder. Owned server stopped afterward.
This verifies skeleton registration only, not production graph execution.
Phase 6/7 acceptance is partial: real coder/judge, presentation preparation,
negative new-file compilation, complete governor wiring and accepted completion
remain unverified. No framework commit or push was made.

Further Phase 7 progress: twelve frozen constraints tests failed against the
stub before implementation, then passed. `core/constraints.py` prepares accepted
managed-block bytes from trusted review state, checks exact candidate/version and
the original AGENTS.md hash, requires approved evidence provenance, deduplicates
normalized statements, keeps 40 active entries and archives overflow. Human text
outside markers stays byte-identical. Preparation has no filesystem effects;
metadata-only Git completion and production executor wiring remain unimplemented.
Task 11.3 remains open until that commit ancestry is verified as well.

Final fresh offline suite for this checkpoint: 307 passed, one existing warning,
exit 0. All 27 frozen manifest entries match. Nested repositories have no tracked
drift; demo and helper files are new game-local overlays. The outer host reports
ProjectSettings/boot.config modified, while git diff reports no content diff and
warns about LF/CRLF conversion. Automatic approval review rejected a scoped
git restore because the standing rule prohibits destructive filesystem commands
outside the framework repository. No restore occurred; leave this host drift
for explicit user approval rather than bypassing the rejection.

## Branch recovery and accepted completion (2026-11-17)

The user explicitly approved restoring boot.config and granted standing clearance
inside the dedicated host folder. The scoped restore succeeded and tracked host
status is clean. Existing game test failures remain deferred; the original
interactive project is outside this authorization.

Five new branch tests failed against a stub, were hashed into frozen-tests.json,
then passed after implementation. Abandonment journals intent, detaches only a
registered clean integration worktree to its baseline, retains the cycle tip,
preserves starting user edits, and reconciles a crash after detach. Changed refs,
foreign branches and unexpected worktree changes stop rather than being discarded.

Four completion tests followed the same RED/freeze/GREEN sequence. Completion
requires an authenticated exact-candidate approval and matching committed file
hashes, builds an isolated Git index, creates a direct child containing only the
managed constraint change, and journals before compare-and-swap publication.
Recovery after publication reuses the same commit, then completes review output.
An inline review finding produced an additional RED/frozen integrity regression:
a changed journal commit previously reached publication before blob rejection.
The implementation now compares the entire expected completion tree before any
ref update. No frozen tests were revised to accommodate implementation behavior.

Commands: `uv run pytest -q tests/test_branches.py tests/test_budget.py
tests/test_constraints.py` (27 passed); completion and integrity checks plus
those governor tests (32 passed); fresh `uv run pytest -q` (317 passed, one
existing collection warning, exit 0). All 30 frozen manifest entries match.
`git diff --check` passes. The graph dev server compiled and /assistants/search
listed unity_coder; the owned server was stopped. This remains skeleton
registration, not executor acceptance.

Tasks 11.1 and 11.3 are complete; progress is 46/61. Task 11.2 and Phase 7 as a
whole remain partial: production budget exhaustion must still connect to worker
reconciliation, abandon evidence/dossier and final lifecycle wiring. Real model
IDs are empty in local configuration and no provider credential setting was
found; provider/coder/judge selection was requested without asking for secrets.
No new dependency, framework commit, mainline write or push was introduced.

## Local AI configuration and provider boundary (2026-11-17)

Loaded the user's ignored ai.local.toml without exposing credentials. Added the
OpenRouter blocking transport, strict required-parameter routing, no redirects or
automatic retries, bounded time/output, sanitized errors and secret-free repr.
Preserved the user's explicit judge effort setting. Twelve configuration/transport
tests plus one effort test followed RED, hash freeze and GREEN. Added five frozen
paid-call/judge-context tests: reserve before dispatch, reject overspend, retain
uncertain calls, reuse durable replies after crash and exclude coder notes and
authorship fields from the judge context API. All eighteen pass without network.

`uv run python -m unity_coder.ai_check` exited 1: coder connected and returned OK;
judge returned HTTP 404. Public catalog lists both model IDs, but the selected
judge does not advertise temperature support. This suggests strict parameter
routing rejects the temperature-zero request; no raw provider error-body diagnosis
or successful judge invocation is claimed. See live-evidence/model-connectivity.json.
User choice was requested: compatible judge or explicit policy revision. No
fallback/model/configuration change was made. The probe sent no game code.

Fresh `uv run pytest -q`: 335 passed, one existing collection warning, exit 0.
Task 10.6 remains partial: no real coder/judge unit has completed on the Unity
host, and the exported graph is still a skeleton. Existing game failures remain
deferred. No new dependency was added; credentials remain only in the ignored
local configuration. Model transport protocol references are in dev-environment.md.

## Approved judge temperature exception (2026-11-17)

The user explicitly approved provider-controlled temperature for the configured
judge. D-28 supersedes only D-12's mandatory temperature-zero clause; its original
decision entry is preserved. Reconciled the boundary spec and planning artifacts.
Added explicit temperature_mode configuration and included it in durable call
identity. The default remains zero; provider mode omits temperature and retains
reasoning effort. Existing frozen default-zero tests were not changed. Two new
tests observed one intended failure/one pass, were frozen, then both passed.

Applied only the approved setting to the ignored local judge configuration;
credentials and model choices were preserved. The connectivity command exited 0:
both configured models returned OK. Judge effort remains medium. Evidence is in
live-evidence/model-connectivity-approved-policy.json; prior failed evidence is
retained separately. Full offline suite: 337 passed, one existing warning, exit 0.
Task 10.6 remains incomplete until a real unit finishes on the dedicated host;
connectivity alone is not pipeline acceptance. Existing game failures remain deferred.

## Real coding units, live compile inclusion and budget abandonment (2026-11-17)

Executed `uv run python examples/isolated_demo/real_models.py` with fresh
DEMO_ATTEMPT=live1, the dedicated host and the existing frozen fixture. Exit 0.
Both configured models were used through ModelCalls and the durable budget ledger;
the coding requests overlapped in separate worktrees. Fresh EditMode baseline:
five assertion failures. The independent judge classified A and B separately as
implementation defects, receiving criteria, specification, mechanical evidence,
ownership and full source/test text, but no coder notes or model authorship.
Coder output was validated as owned-file JSON and applied through ExecutionHost.
Integrated Green: five passes. Real coder Refactor review followed; confirmation:
five passes. Both TDD states are complete, and all frozen test/config/metadata
hashes match coding worktrees, integration and host. Usage: 2,414 input and 3,855
output tokens. Raw request-specific results and concise summary are in
live-evidence/real-model/. No human acceptance or exported-graph execution is claimed.

Six model-output tests observed meaningful RED, were frozen, and passed after
implementation. Core parsing rejects unowned paths, malformed file content,
missing refactor rationale and non-defect judge verdicts. No stack behavior was
added to core; the opt-in rehearsal supplies the Unity fixture context.

The new-file compile probe produced its unique #error diagnostic, proving source
inclusion. Its first recovery timed out during a domain reload blocked by a
ParrelSync promotional dialog. Computer-use inspection found and closed that
dialog. No package/source workaround or editor restart was used. A fresh request
then compiled successfully and passed all five fixture tests; its snapshot equals
the exact successful real-model candidate. Temporary probe/source metadata are
gone. The timeout evidence is retained alongside successful recovery, not rewritten
as success. Compile callbacks took 1.092 seconds for negative inclusion and 0.790
seconds for recovered success, excluding refresh/reload/dialog time. Commands and
scope are recorded in dev-environment.md; evidence is in live-evidence/compile-inclusion/.

Recorded current branch/revision/clean status for all 14 host repositories and
hashes for packages manifest/lock, project version and installed verifier/asmdef.
The game mount is its independently verified repository, external coding trees
are outside Assets, installed helper bytes match the packaged source, exact-project
Bridge identity and reload recovery are verified. No tracked host or nested-module
drift remains. See live-evidence/host-readiness.json. This completes 10.9/10.10
readiness requirements; the original game tests were not rerun or changed.

Continued implementation with BudgetGovernor: four frozen tests failed before
implementation and now pass. It atomically stops new reservations, preserves the
exhaustion snapshot, requires trusted worker reconciliation before Git transitions,
retains candidate refs, writes a budget dossier with no invented unit defects and
publishes abandon. Late usage reconciliation cannot restart paid dispatch;
repeated abandonment is idempotent. Combined governor/accounting/branch/completion
checks: 28 passed. Fresh full suite: 347 passed, one existing collection warning,
exit 0. All 36 frozen manifest entries match. The dev graph compiles and is listed;
the owned server was stopped. No framework commit or push was made.

Progress: 53/61. Phase 6 component/model/live-worker criteria are met except 10.3
presentation preparation; phase 6 as a whole is not complete. Phase 7 component
acceptance is met: accepted metadata-only completion and budget abandon are tested
with real disposable Git repositories and fake human/worker boundaries. Production
graph/CLI wiring and the delegated OpenSpec boundary remain outstanding, as do
real presentation/HITL replacement rehearsals and final whole-system review.
# Delegated boundary component checkpoint — 2026-11-17

- Task 12.1 complete; pinned apply instructions confirm 54/61 tasks complete.
  Tasks 12.2 and 12.3 remain open; this is not production delegated execution.
- RED: `uv run pytest -q tests/test_architect_boundary.py` exited 1 because the
  requested boundary module did not exist. Freeze recorded before implementation.
- Additional RED: `uv run pytest -q tests/test_boundary_reconnect.py` exited 1:
  3 failed, 2 passed. Existing progress incorrectly requested start rather than
  resume, and the context-export CLI was absent. Freeze recorded before fixes.
- GREEN: `uv run pytest -q tests/test_architect_boundary.py tests/test_boundary_reconnect.py`
  exited 0, 30 passed. Coverage includes schema/context discovery, original-source
  provenance, task identity, invalid formats, progress reconnect, all non-pass
  outcomes, accepted-review identity, unmapped tasks, implementation repair and
  contract rework routing. Review records in these tests are trusted-host fakes,
  not real human acceptance or production Git ancestry evidence.
- `uv run pytest -q` exited 0: 377 passed, one existing TestResult collection
  warning. All 38 frozen file hashes match. No frozen tests were revised.
- Actual pinned CLI output passed discover_context: superpowers schema, five
  artifact groups, 61 tasks, two explicitly selected source references. Export
  contained no machine root. No new planning system or custom schema was created.
- `uv run langgraph dev --allow-blocking --no-browser --port 2025` initially
  failed inside upstream OpenAPI loading under Windows GBK. With PYTHONUTF8=1,
  it started successfully; POST /assistants/search listed unity_coder. The owned
  process was interrupted and no listener remained. This verifies the existing
  bootstrap graph only, not production execution.
- Inline self-review found the reconnect/start ambiguity, now covered by a frozen
  regression. Current components rely on trusted host-owned state and the existing
  ReviewGate/CandidateCompletion gate; they do not authenticate humans themselves.
  Same-run consecutive-cycle transition and production callback assembly remain
  implementation work. No external dependencies were added.
- CLI export-context/status and the maintained framework-apply skill are present;
  there is no production run command yet. The worked boundary cycle is documented
  in docs/boundary-contract.md. Eligible task IDs remain advisory to the Architect.
- No Unity host or original game files were changed. Previously deferred game
  failures remain deferred. UI baseline preparation, live exact-candidate human
  review, artist replacement rehearsal and final compliance review remain unmet.

