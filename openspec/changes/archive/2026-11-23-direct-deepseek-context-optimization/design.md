# Design

## Context

See `proposal.md` for motivation and the two delta specifications for observable
requirements. This design targets the existing isolated backend checkout and
external trusted state selected by `LOBBY_RUN_ROOT`, with the enclosing checkout
as the existing OpenSpec planning home. Paths below are relative to their named
roots. No machine paths or secrets belong in exported artifacts.

The current host's `ContextWorkers` already owns context curation, review dispatch
and target recovery. `ModelClient` and `ModelCalls` provide the extension boundary
for new clients and existing accounting; `CodexPolicy` accepts explicit role and
effort. `actual_judge_feedback.py`, `codex_review_reuse.py`, retained-call validators
and `codex_lobby.py` contain historical medium-effort or dual-Codex assumptions.
They must validate historical policies against their original grants and future
policies against a new grant. Historical receipts must never be edited to fit it.

The current run is stopped operationally. The latest result identifies candidate
`625db77bf4e75060435947d955328a729f6f87dc`, version 70. The later stopped
operation and every newly uncertain call must be inspected during implementation;
neither the old progress report nor this design is a recovery authorization for
an uninspected effect.

## Goals / Non-Goals

**Goals:** Explicit mixed-provider composition; safe same-run activation; fewer
avoidable Judge input tokens; direct paid-call accounting; complete evidence
provenance; compact but expandable Architect handoff; measured quality and cost.

**Non-Goals:** Rewriting core graph, coordinator, budget or contract schemas;
changing game implementation or any of the 199 frozen files; replacing tests with
summaries; putting trusted state under Unity imports; copying provider keys;
changing the Architect's own model; automatic model/effort fallback; guaranteeing
semantic equivalence of arbitrary prose compression; promising zero Judge input
growth on complex cases; fixing unrelated performance/runtime defects.

## Decisions

### 1. Use host-local mixed clients with explicit policy epochs

Implement a new host-local direct client conforming to the existing client
interface. It owns DeepSeek request dialect, response validation and sanitized
transport errors. Do not broaden the shared TOML loader or pretend that
`provider='openrouter'` is direct DeepSeek. Compose coder/optimizer clients and
the existing Codex Judge independently instead of the present all-or-nothing
backend selector. Add a portable proposed profile to the new change and activate
a hashed local copy in external trusted state only during apply.

| Component | Route | API model / identity | Effort | Initial output allocation |
| --- | --- | --- | --- | --- |
| Coder: test authoring, Green, Refactor, format repair | Direct DeepSeek | `deepseek-flash` | low, thinking enabled | Existing 65,536 per stage |
| Context selector, separate isolated calls | Direct DeepSeek | `deepseek-flash` | low, thinking enabled | 8,192 |
| Judge: test review and defect routing | Existing Codex app-server | `gpt-6.1-sol` | low | Existing 32,768 |
| Architect | Existing user session | unchanged | unchanged | No new implicit allocation |

These are proposed dispatch reservations, not aggregate grants. Direct HTTP sends
the verified Chat Completions dialect: `thinking.type=enabled`,
`reasoning_effort=low`, `max_tokens` for the explicit completion allocation, and
no OpenRouter `provider`/`reasoning` object. Request strict JSON output and validate
the returned object, completion status and usage; valid JSON alone is insufficient.
The current Chat Completions reference confirms `max_tokens`; recheck at pilot. Omit
temperature for DeepSeek thinking mode because it is ignored, and retain the
Judge's already approved provider-controlled temperature. Record this explicitly;
do not claim deterministic sampling. No tools are sent.

The local secret source is the existing Git-ignored `ai.local.toml`, as explicitly refined by the user; its `[coder].api_key` is read in the trusted host only.
Optional OS-backed secret retrieval can be added later, but no new secret store
or dependency is needed now. The endpoint is allowlisted to the official direct
HTTPS origin; verify normal certificate checks, refuse redirects and proxy/routing
overrides not approved in the existing direct-only policy. No credentials appear
in subprocess arguments, source, model input or diagnostics.

The profile records API alias and observed concrete version. As of the planning
date, official docs map Flash to V4.1-Flash-1017. Verify authenticated model access
without generation first. Accept only a documented observed response mapping;
unexpected alias evolution stops admission until an explicit policy revision.
Preserve valid usage even on rejected identities or length-truncated output.

All future Coder effort overrides are explicitly low, including units formerly
configured as none. All future Judge calls are low. Old medium/none receipts remain
verifiable under their historical policies. Reuse rules include the new policy
hash, effective model, effort and prompt identity; no medium receipt becomes a
low receipt. The optimizer's semantic role is recorded in additional backend
identity metadata and operation purpose; it uses the Coder-side accounting client
with a distinct call ID, not a new contract coding unit.

### 2. Build canonical packets from trusted evidence, not Coder messages

The adapter sits on review input assembly, including `review_tests` and `judge`,
before paid Judge dispatch. Its source is the immutable candidate, validated
contract and actual mechanical receipts. It never reads worker `reason`, hidden
reasoning or completion claims as Judge evidence. Strip ownership author names
while retaining required unit IDs and file-to-unit ownership.

```text
immutable source + contract + actual verification receipts
                         |
                         v
              canonical evidence manifest
                         |
                         v
          deterministic exact packing + required closure
                         |
           +-------------+------------------+
           |                                |
     no useful optional set           optional evidence catalog
           |                                |
           |                         DeepSeek selector (low)
           |                                |
           |                    validate IDs / hydrate exact bytes
           +-------------------+------------+
                               |
                               v
                    mandatory coverage guard
                               |
                               v
                   Judge (GPT-6.1 Sol, low)
                               |
                 exact verdict + compact finding index
                               |
                               v
                      Architect / native routing
```

Canonical packet fields: format version; run/contract/candidate/unit/stage;
policy hashes; required criteria and spec item IDs; mechanical evidence with
original request identity; complete ownership; current patched file set; referenced
test/fixture/API source; optional catalog; unresolved earlier findings relevant to
this operation. Use a host audit hash separately from the Judge content: model
brand, call IDs or worker attribution that reveal Coder identity stay out of its
prompt. Source comments are data, not authority.

Each source item has a stable logical ID, relative path, whole-byte SHA256,
kind, source revision, exact UTF-8 byte ranges on valid character boundaries and
dependency IDs. The manifest is hashed with deterministic field ordering. The
host retains canonical bytes and any prior admissible prompt, so optimization
is auditable and reversible. Store under an external
`context-packets/<canonical-hash>/` namespace. Do not replace runtime evidence
paths or persist secrets from arbitrary local configuration into the catalog.

### 2a. Return optimized input and explicit check results together

Host means the trusted Python execution program composing LangGraph, provider
clients, persistent budget and verification services. It is not an AI model.
Context optimizer means the complete adapter: deterministic packing, optional
DeepSeek selection, exact hydration, validation and reporting. The DeepSeek call
alone cannot certify its own output.

Each optimizer invocation returns one versioned `OptimizationResult` containing:

- `optimized_input`: the exact candidate Judge/Architect packet, or null when blocked.
- `check_results`: per-check identifier, `pass`/`fail`/`unknown`, evidence references,
  verifier kind (`code_verified` or `model_reported`), and concrete reasons.
- `decision`: `use_optimized`, `use_original`, or `blocked`.
- `canonical_sha256`, `optimized_sha256`, source/coverage manifests and unresolved dependencies.
- Original/delivered bytes and token counts or labeled estimates; selector usage,
  reduction ratio, cost assumptions/unknowns, expansion and fallback reasons.

Checks cover required-item completeness, source-byte integrity, dependency closure,
authorship/secret filtering, policy identity, savings qualification and budget.
Code-verified checks control admission. Model-reported checks are advisory only.
Unknown or failed correctness checks prohibit optimized delivery; return the exact
original admissible packet with `use_original`, or `blocked` if it cannot fit or
accounting is uncertain. The Host validates result identities and executes the
reported decision; it never reconstructs a pass from a prose success claim.
Persist the result before downstream dispatch, including bypass/fallback/blocked
paths, and show the same report to Architect. Raw payloads stay in trusted storage;
user-facing reports carry nonsecret metadata and references.

### 3. Protect the required closure before any cheap model runs

The full current bodies of every patched file in the integrated operation are
mandatory, even for review of one unit. Supply exact applicable spec clauses,
all its acceptance IDs and the complete relevant ownership map. Inherited context
must distinguish current files from prior proposals; duplicate stale proposals
are optional unless needed to explain a regression or restore provenance.

| Review type | Mandatory evidence |
| --- | --- |
| Single-owner compile failure | Gate/status/behavioral flags, all compile diagnostics and related owners, complete patched files, affected API/assembly contract, ownership and criteria/spec clauses |
| Assertion failure | Above source/criteria plus every selected/executed/failed ID with counts, exact assertion messages and failure kinds, all failing test bodies, setup/teardown/assertion helpers, shared service dependencies and relevant passing regression constraints |
| Mixed runtime/assertion failure | All failure evidence retained, including runner/setup distinctions and exceptions; never relabel as valid behavioral Red or Green |
| Test-validity review | Complete reviewed owned test files, mappings, assertions/helpers/fixtures and relevant production interfaces/spec; no skipped body hidden as an excerpt |
| Architect rework | Every unresolved unit finding and retry trend, original classification/explanation, candidate/contract/evidence identities, budget and requested boundary decisions |

The host computes source dependency closure conservatively. Use existing adapter
syntax facilities where available; uncertain reflection/dynamic references,
shared partial classes, unknown helper resolution or unsupported syntax promote
the implicated full files to mandatory. Do not rely on model-selected lines or
lexical symbol matching as proof of completeness. If a safe scoped closure is
unknown, use the full admissible canonical context. Hash-only references never
stand in for code Judge is required to read.

Deterministic packing removes repeated serialized bodies, repeated host-added
instruction blocks, duplicate metadata and irrelevant generated inventory detail.
Do not remove code comments or minify C# strings, indentation-sensitive text or
hash-bound anchor source. Multiple identical diagnostics retain occurrence and
test relationships. Stable rules/spec first and changing candidate/evidence later
improve prefix caching without sharing Coder conversation or private state.
Cache hits remain input tokens in the run ledger.

### 4. Restrict DeepSeek to optional evidence selection

Do not ask for a prose summary. Supply the immutable optional catalog and raw
source chunks needed to assess it, together with required criteria and mechanical
identities. A separate fresh Flash/low call returns strict JSON: canonical hash,
schema/policy hash, selected item IDs, allowed exact ranges and criterion coverage
IDs. It cannot add code, natural-language facts, exclusions of required items,
classifications, confidence, verdict hints or policy changes. Audit omission
reason codes locally; do not forward selector commentary to Judge.

The host validates unknown/duplicate keys and IDs, paths, ranges, source hashes,
coverage and closure; then hydrates exact canonical source. Mandatory content is
inserted independently, whether the selector requests it or not. Explicitly test
malicious attempts to suppress a cross-unit cause, passing regression, exception,
test helper or conflicting requirement. A request to read arbitrary files is
invalid. The optimizer can neither edit the candidate nor call tools.

Proposed configurable defaults: skip the paid selector below an estimated 16,000
Judge input tokens or when less than 20% of deterministic input is optional.
One selector attempt per canonical/policy hash, no automatic format retry. Cache
the validated selection by exact content and policy; cache validity is distinct
from reusing a Judge verdict. When tokenization is unavailable, byte-based bounds
are marked estimates and actual reported usage is authoritative.

After selection, require at least 20% estimated Judge input reduction from the
canonical baseline before spending an optimized Judge call. If the canonical
packet is already short or mandatory-heavy, use deterministic packing alone.
These thresholds are proposed rollout policy, not permission to remove necessary
items. Do not pay an optimizer repeatedly to chase a compression ratio.

### 5. Keep Judge authoritative and allow exact expansion

Adapt the host's internal review wrapper, leaving native return schemas unchanged.
The first response is either a strict context request or a final native review
object. A context request names canonical item IDs and a reason code, has no
defect verdict and cannot change ownership. At most one expansion round supplies
all requested exact content plus dependency closure. The next response must be
a complete native final object; otherwise fall back to the full canonical packet
or stop if full context has already been tried. Every paid request has its own
identity/reservation and a final decision is linked to its complete context.
Tool-disabled Codex sessions stay tool-disabled: retrieval is a host-controlled
request/response exchange, not a file-read or arbitrary tool capability.

Maximum per uncached review is one selector plus three Judge calls: optimized,
expanded and full canonical fallback. Reserve enough of the existing budget for
that bounded path before its first dispatch. If this cannot fit, bypass optional
selection and reserve canonical review alone, or report budget exhaustion. Do
not spend selector tokens and then silently fail to budget the needed Judge.

Invalid selector output with known settled usage falls back deterministically.
Unknown selector/Judge usage stops for reconciliation; it does not immediately
trigger another paid call. Failed expansion or disagreement is not a contract
defect in the game. Mandatory-capacity overflow stops with exact input/capacity
identities instead of summarizing patched files.

### 6. Make Architect handoffs compact without rewriting findings

Use deterministic records for each unresolved finding: unit/criterion, exact
classification and explanation, gate/failure IDs, evidence and source references,
retry trend, unresolved decision, and candidate/contract hash. Include aggregate
accounting snapshot and original dossier reference once per handoff. Identical
supporting diagnostics appear once with a relationship table; resolved history
uses references. The original verdict and dossier remain immutable authority.

For ordinary short Judge replies, no model call is justified. For large repeated
supporting bundles, the same optional-source selector can reduce supporting
attachments; it cannot rewrite explanations or unresolved requirements. The
Architect receives a concise index first and hydrates exact bodies as needed.
Host-to-Architect artifact delivery is selective: do not send every historical
report in full. This can reduce information resent in a future model turn; it
cannot retroactively remove tokens already in this chat or guarantee changes to
Codex's own internal context management.

### 7. Account for total cost, not just a shorter expensive prompt

Every direct Coder, selector, Judge, expansion, pilot and audit call uses the
same `BudgetLedger` and unique purpose-scoped call identity. Selector calls use
the current unit identity plus `context-select` purpose, never add graph units
or consume a game repair attempt. Store receipts with complete requested/returned
model identities and reasoning policy. Provider usage counts all billable output;
record reasoning/cached breakdowns when reported without double counting.

Budget limits remain 250,000,000 input / 24,000,000 output / 160 cycles / 2 added
units. The status snapshot of 160,700,047 / 6,517,038 is historical observation,
not an allocation reset. Reconcile the latest ledger and preserve every unresolved
reservation, including any one added after the last known set of 26.

Compute a per-packet report: canonical and delivered bytes; exact token counts or
labeled estimates; actual selector input/output; actual Judge input/output for
all calls; cache-hit/miss and reasoning details; latency; fallback/expansion count;
coverage guard result; estimated or measured total cost. Money uses dated prices
and known billing units. Codex subscription/quota consumption has no universally
verified per-token dollar price: report token/quota proxy and incremental DeepSeek
cash separately, never advertise those as measured dollar savings.

As verified on the planning date, official Flash pricing is $0.15/$0.30 per
million cache-miss input and $0.60/$1.20 output off-peak/peak. Hit pricing is lower.
Rates are descriptive, not pinned forever. The general break-even condition is:

```text
selector cost + optimized Judge cost + expansion/fallback cost
    < canonical Judge cost
```

Cheaper input can still cost more overall if selection is repeated or Judge
needs more reasoning/expansion. If prices are unknown, qualify token reduction
and quality only, and explicitly leave monetary savings unproven. Low effort
reduces a configured reasoning request, not a guaranteed output-token quantity.

### 8. Qualify packet classes before active selection

Freeze offline unit/adversarial tests before helper implementation. Include at
least twelve source fixtures spanning every review class, long Chinese and
Unicode source, repeated failures, cross-owner coupling, partial helpers,
dynamic/reflective dependency, contradictory requirements and prompt injection.
Define expected evidence closure and adjudicated defect routing independently
from optimizer outputs. Do not let Coder author its own expected verdicts.

Run a bounded paid pilot under apply authorization: one direct Coder protocol
fixture, and four representative packet classes reviewed with the exact same
GPT-6.1 Sol/low policy using canonical versus optimized inputs. Up to four
selectors and eight baseline/optimized Judge calls constitute the initial
comparison; any expansion counts within the same envelope. This is not approval
of the game candidate. Pilot defaults: a maximum additional reservation envelope
of 10,000,000 input / 512,000 output inside the existing totals, not extra budget.
Stop if conservative reservations cannot fit; change the pilot only through an
explicit reviewed revision, not by shrinking evidence. No per-call Codex hard
cap is claimed; the user's dispatch-accounting waiver remains intact.

Qualification gates:

- Zero mandatory-source omissions or modified source bytes; every malformed or
  injection fixture rejected or expanded, never admitted as trusted evidence.
- Correct expected routing on the adjudicated corpus for both canonical/low and
  optimized/low; investigate all disagreements. If canonical/low itself fails,
  stop and report that the requested Judge effort failed quality qualification.
  Never silently revert to medium or accept agreement as sufficient truth.
- Target at least 40% median measured Judge-input reduction across compressible
  pilot classes; a class needs at least 20% actual reduction and no correctness
  regression for active selection. Unqualified classes use deterministic/full
  context. Missing exact token estimates are replaced by actual pilot usage.
- Where actual monetary prices are available, require at least 10% net cost
  reduction for paid-selector activation, including its overhead and expansions.
  Without a Judge cash price, label dollar savings unproven; activate only on
  token-quality gates and show the added direct-API expense to the user.
- No more than one expansion; any unexplained omission or wrong adjudicated
  verdict disables that class pending investigation. Mandatory-heavy classes
  have no compression obligation and stay canonical.

For the first ten active reviews, log all coverage checks and exact-packet sizes.
Perform one scheduled canonical/low shadow audit in that window if the pilot
envelope and remaining aggregate budget cover it. If the audit cannot fit, keep
model-assisted selection in shadow/deterministic mode until it can be qualified;
do not hide the missing audit. Audit disagreement disables that class. This
small pilot is evidence of bounded qualification, not a proof of all future
semantic equivalence.

### 9. Keep the existing native lifecycle and immutable identities

Use a new hashed activation profile/grant, not an in-place rewrite of historical
Codex pilot grants. The ignored `ai.local.toml` is updated as the user requested,
with its previous bytes backed up locally. The current user choices authorize the
proposed future role configuration; this planning workflow does not activate it.
During apply, preserve a Git checkpoint on the isolated non-mainline branch and
a read-only snapshot of run identities before any host changes.

Native operational resume uses the reconciled current stop, new model-call IDs
and retained prior effects. Do not change the runtime contract just to change a
provider; if genuine product rework is needed, use the normal consecutive cycle
transition without resetting budget or freeze. Expired locks are reconciled using
live process identity, never removed blindly. New helper tests are separate from
the frozen lobby tests. Unity remains single-writer and sequential with original
baseline/import checks. The adapter's path case rules remain authoritative.

Validation matrix:

| Area | Required evidence / owner |
| --- | --- |
| Direct-provider request/response | Frozen host tests with mocked network, then direct pilot receipt |
| Low-effort independent Judge | Effective Codex policy and genuine SDK receipt; host policy validators |
| Packet integrity | Frozen deterministic/adversarial fixtures; exact source/hash/required-set comparisons |
| Coder boundaries | Existing ownership, anchor, syntax and 199-file freeze checks |
| Retry/recovery | Interrupted before/after submission simulations; append-only history/account equality |
| Cost and quality | Same-Judge/low paired receipts plus adjudicated findings and dated cost report |
| Lobby continuation | Native actual results and final selected Unity tests; independent Judge remains mandatory |
| Human review | Exact final candidate package; only the user can approve |

## Risks / Trade-offs

- Cheap selector shares a model family with Coder: no notes enter selection,
  mandatory evidence bypasses it, output is extractive, and independent audits
  challenge omissions. Optional omissions can still bias attention; no absolute
  semantic-preservation claim is made.
- Incorrect dependency closure: promote uncertain scopes to full files; deterministic
  source guards and adversarial tests precede paid savings goals.
- Model alias or parameter drift: verify official docs and actual returned identity
  at pilot; unsupported semantics block activation rather than route elsewhere.
- Low Judge effort misses subtle defects: adjudicated comparison gates activation;
  any need for higher effort is reported to the user, never automatic.
- More calls and paid output erase savings: skip small packets, cache exact plans,
  measure end-to-end overhead and disable uneconomic classes.
- Token accounting can appear lower from cached input: keep raw actual usage and
  pricing breakdown separate; never refund cached input from the run ledger.
- Generic helper assumptions break on mixed providers: audit both-Codex checks,
  medium-effort constants and historical validation; test before native recovery.
- Current host latency remains high: preserve strict scans and report it separately;
  input optimization does not fix the progress journal or repeated full audits.

## Migration Plan

Latest user sequencing: finish backend implementation and qualification before
returning to frozen lobby conflicts. Preserve the current invocation to a native
boundary, then perform backend-only protocol and exact-source audit calls. Do
not begin a new product contract or mutate lobby tests for this closeout. The
first-ten-review observer remains persistent and continues counting when the
lobby resumes; report its actual count rather than fabricate additional game
reviews. Reaching `awaiting_human_review` remains an existing lobby obligation.

Implementation refinements preserve the approved evidence policy: packing format
2 uses short body-reference IDs with explicit full hashes and exact byte lengths.
Free exact packing keeps positive reductions below the paid selector's 20% gate;
expansions are rejected. The pilot/audit sub-envelope counts declared qualification,
selector and extra-review purposes; ordinary coding and initial product review
remain fully charged to the aggregate ledger. An immutable scope record binds
this attribution to the original envelope without resetting its call baseline or
limits. A new packing format requires fresh paid IDs and qualification rather
than reuse of the old format's approval.

Final source filtering excludes all Coder-owned narrative reports before packet
construction. Misclassified private reports are blocked by the optimizer and
consumer, with explicit failed checks. Live source strings are checked against
committed raw bytes, preserving CRLF. The final clean shadow audit uses a genuine
archived compiler failure and 74 complete runtime/profile sources; its paired
results agree. Historical mixed packets are retained but do not authorize the
new source-filter policy. Current routing requires source-filter version 2 and
preserves the previous activation bytes in immutable history.

1. On explicit apply, inspect current live status, effect journal, full reservation
   set and exact stopped candidate. Save current isolated branch and source hashes.
2. Author/freeze new offline tests; implement host-local clients and context adapter
   with no runtime or lobby-test changes. Run offline regression and compile/list
   the unchanged graph as the repository's framework verification requires.
3. Resolve the local key, verify exact direct model and Codex low availability,
   prepare the immutable canonical corpus and reserve the bounded pilot envelope.
4. Run the paid protocol and paired quality/cost pilots. Publish real receipts,
   failures, expected findings and eligible classes. Do not reset the envelope
   after failure or count an unknown call as free.
5. Register the new role/context policy and preserve old grants/receipts. Reconcile
   every old uncertain effect through existing trusted recovery. Validate no frozen
   or overlay-source drift; stage changes through public native recovery only.
6. Activate direct Coder and low Judge. Enable deterministic packing globally,
   model-assisted selection only for qualified packet classes. Complete backend
   proof and preserve the game's native boundary; the user deferred product rework.
7. Publish backend usage, estimates, check results and exact implementation
   revision. Retain the lobby's separate obligation to reach human review after
   its contract conflicts are resolved; never approve it for the user.

Rollback disables selection for future calls and restores full canonical packets
without reverting source or history. If the new provider itself fails, stop
operationally; returning to Codex or a different model/effort needs explicit user
authorization and a new policy identity. Invalidate affected derived decisions
and re-review from complete evidence. Do not replay old calls, refill budgets,
delete reservations or modify previous-run records.

## Open Questions

- Actual direct DeepSeek credentials and account/model access are unverified until
  local setup; the key must be entered through the local secret reference.
- Exact local token counting and subscription dollar equivalents may be unavailable.
  Use declared estimates and measured provider usage, with monetary claims clearly
  limited; no dependency or fabricated dollar rate is implied.
- Current active stop may contain a newly uncertain effect beyond the previously
  registered 26. Reconcile its exact evidence during apply; never assume its usage
  or cause from a stale status summary.

These are implementation/measurement gates, not unresolved product requirements.
This design does not require changing any settled framework decision.

## Provider references

Checked on 2026-11-23: [models and prices](https://api-docs.deepseek.com/quick_start/pricing/),
[thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/),
[context caching](https://api-docs.deepseek.com/guides/kv_cache/),
[Chat Completions fields](https://api-docs.deepseek.com/api/create-chat-completion/).
