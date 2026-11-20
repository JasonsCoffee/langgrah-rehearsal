# Opt-in Codex worker backend

## Authorized lobby activation update

The user has now explicitly approved Codex without forced per-request token caps.
The profile-bound trusted grant is recorded, and the real two-model pilot passed:
10,152 input / 123 output tokens settled in the existing ledger. The production
host passed the original 81,134-file baseline/import audit and native recovery
resumed cycle 60, preparation step five. See the active change's
codex-migration-report.md. The earlier inactive observations below are history;
this update does not claim completed lobby implementation or human acceptance.

The pre-change framework/rehearsal checkpoint is 6ff8d8b. The separate resilience
amendments remain preserved at 826b425; they are not silently activated in a pending
lobby operation. This change supplies a programmatic Codex worker boundary, with
fresh Coder/Judge sessions consuming the same exported requirements and candidate.
The Judge receives no Coder reasoning/history and must use a different model.

## Budget and activation contract

The installed Codex protocol exposes thread token-usage notifications, but no hard
per-request input/output token controls. A thread goal budget is not treated as
an inference completion cap. The default require_hard_caps mode therefore rejects
before budget reservation or model dispatch. No capability is inferred from a
model name, advertised context size or successful metadata request.

An alternative dispatch_accounting mode needs a separate explicit trusted-user
authorization bound to the immutable role/model/effort policy hash, a portable
provenance reference and a persistent maximum number of calls. This mode preserves
the native aggregate ledger and charges all reported actual usage, including
provider overruns; unknown calls retain their full reservations. It cannot claim
a server-enforced per-request generation cap or zero possible budget overshoot.
It is not active for the lobby. Approval to investigate the backend alone does
not grant this weaker enforcement mode or change model/effort settings.

Backend/policy identity and framing allowance are part of new native paid-call
identities. Historical OpenRouter identities/reservations remain unchanged.
Each call uses an isolated fresh session, read-only sandbox, no MCP/app/shell/web
or nested-agent capabilities, no user-history fork, and a bounded deadline. The
host alone applies returned patches through existing ownership/freeze gates.
Actual session usage and session/turn IDs are persisted before returning a model
reply. Tool activity, model rerouting, missing usage or ambiguous completion stops
without automatic replay. The trusted authorization callback is not model-facing.

The current lobby stays stopped at operational cycle 60, candidate
0519b568003ae4f820122ec8ef94016a068597f2. All existing usage, sixteen uncertain
reservations, the 100m/12m/80 aggregate limits, overlay and frozen-test rules stay.
Activation requires a successful isolated worker/usage/isolation trial, explicit
model and budget policy approval, and native operational recovery using new call
IDs. No invocation is allowed to manufacture a Judge result or human acceptance.

## Acceptance evidence

Twenty-five new cases failed and one legacy-compatibility case passed before
implementation. Frozen regression SHA256: `a885b2c421af3bdc90a1cbc03497e0e113d8ce28ecc38d4bff8a51298f515324`.
All tests use fake exchanges and disposable state. Real metadata inspection used
Codex 0.169.0-alpha.11.1, authenticated account type chatgpt, model/list and
account/read only; no thread or turn was started. Models include gpt-6.2-sol
(low supported) and gpt-6.1-sol (medium supported). No credential was displayed.

No dependency is added. Full offline tests, graph compilation/listing, changed-file
hygiene and exact lobby preservation must pass before any activation proposal.

Protocol test revision 2 corrects an invalid wire expectation discovered by the real metadata-only startup: Codex CLI treated a quoted MCP key as a distinct server and rejected it with invalid transport. The original protocol-test SHA256 was `b51fc44a72f34ea808b437818d4f801b09e61ef10e5e7b97a7eba267169421eb`; the corrected frozen SHA256 is `9869bd49a9d9933b7964dc0e38918334a0dc835e1a29ca7eac97af403029ae55`. The amendment retains the requirement to disable every configured MCP and adds fail-closed cases for ambiguous names. No lobby frozen test changes.

The real corrected ephemeral-session metadata check succeeded: explicit gpt-6.1-sol, provider openai, sandbox readOnly/networkAccess=false, approvalPolicy=never, and the isolated working root matched. No inference turn started. Sanitized evidence: codex-worker-preflight.json. Proposal: ../openspec/changes/rehearse-monopoly-game-lobby/codex-backend.proposed.json. This profile has no authority by itself.

Codex also controls request temperature internally; this protocol exposes no temperature override. The proposed profile explicitly records Codex-native temperature behavior, so it does not claim to preserve the old Coder temperature=0 transport parameter. Role models and efforts remain explicit.

## Final code-only verification

The final framework suite passes **583 tests** in 233.16 seconds, with the existing
TestResult collection warning. All **138 existing rehearsal wiring checks** pass.
The graph compiled and `/assistants/search` listed `unity_coder`; the development
server was stopped without submitting a run. No dependencies changed. New source
and documentation pass diff hygiene. The pre-change checkpoint and separate
resilience-fix commit remain saved, and original checkout files are untouched.

There are 45 new offline cases: 26 backend/accounting, ten protocol/isolation, one
rejected-stream cleanup, and eight pilot-consent cases. The protocol suite has the
explicit evidence-backed revision above; all final hashes are recorded in
codex-backend-validation.json. Real SDK checks were metadata-only; actual inference
usage, returned patch behavior and the two-model round trip still need the
explicitly authorized pilot. No Codex inference turn has been started.

The same-run pilot is `examples/codex_backend/lobby_pilot.py`. Its `--check` reports
not ready without the trusted profile-bound grant. It makes exactly one Coder and
one independent Judge calibration call, uses the existing native run budget and
lease, and records actual usage/receipts. Its output cannot accept lobby behavior
or human review. The profile proposes at most 200 Codex calls per role across the
migration; the pilot itself submits at most two calls and has a 60-second deadline
per call. Future production activation remains gated on successful pilot evidence.

Native lobby budget, policy, result, executor, service checkpoint, candidate
selection and overlay manifest remained byte-identical throughout this work.
All sixteen existing uncertain reservations remain. The current run is still
operationally stopped at cycle 60 and is not awaiting human review.

Reference: [Codex App Server](https://learn.chatgpt.com/docs/app-server). The exact
installed protocol, rather than assumptions about future versions, governs the
capability limitation recorded here.
