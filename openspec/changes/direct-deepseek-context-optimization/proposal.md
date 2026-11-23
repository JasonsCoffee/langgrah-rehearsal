# Proposal

## Why

The lobby rehearsal repeatedly sends large, overlapping inputs and has required
expensive recovery around its Codex-backed Coder/Judge route. Use direct DeepSeek
for coding and guarded context selection to reduce paid input while retaining
the evidence needed for correct independent decisions.

## What Changes

- Switch every Coder stage, including test authoring, Green repair, Refactor and
  format repair, to direct `deepseek-flash` with thinking enabled and low effort.
  Use a locally supplied key reference, never a committed key or OpenRouter route.
- Retain Judge `gpt-6.1-sol` through its existing Codex backend, changing future
  calls to low effort. Preserve provider-controlled temperature policy and fresh,
  tool-disabled independent sessions. Do not silently switch the Judge to another
  provider, model or effort on failure.
- Introduce a host-side context adapter: deterministic deduplication and source
  manifests first; a separately accounted direct DeepSeek Flash/low call selects
  optional exact evidence spans when a measured saving is plausible; the trusted
  host validates and hydrates the final packet. Mandatory evidence bypasses the
  selector and cannot be rewritten, hidden or replaced with a summary.
- Apply the adapter to test-source review and defect classification, using
  different required evidence profiles. Preserve all full patched-file bodies,
  acceptance criteria, applicable spec clauses, ownership, mechanical diagnostics,
  failing test identities and effective relevant test/helper source. Exclude Coder
  reasons, private reasoning and authorship signals before selector dispatch.
- Reduce Judge–Architect handoff repetition using a compact deterministic finding
  index and content-addressed original verdict/evidence references. Keep unresolved
  findings, exact classification and original explanation; no model rewrites the
  authoritative verdict. Large optional supporting text may use the same guarded
  selector, but short replies incur no extra paid call.
- Return a single context-optimizer result containing `optimized_input` and
  `check_results`, plus the delivery decision (`use_optimized`, `use_original`,
  or `blocked`). The adapter combines DeepSeek selection with deterministic
  validation; its checks distinguish code-verified results from model claims.
- Record canonical/optimized identities, actual per-role usage, cached-input
  telemetry, cost assumptions, selection/fallback decisions and completeness
  checks. Reuse only exact identity-matching selection artifacts and reviews.
- Migrate the existing stopped run at a native recovery boundary. Reconcile all
  current uncertain effects, preserve every historical charge/reservation and
  budget limit, and use fresh call IDs for changed provider/effort/prompt policy.
  Do not replay completed coding, alter the lobby contract or mutate frozen tests.
- Gate activation with frozen offline adversarial tests, candidate-bound paid
  pilots and a same-Judge/low baseline comparison. Prefer deterministic reduction
  if the paid selector adds no net value. Continue to `awaiting_human_review`
  only in a later explicitly requested apply workflow.

## Capabilities

### New Capabilities

- `model-provider-routing`: Explicit host-local mixed backend role configuration,
  direct DeepSeek request/response accounting and preservation-aware migration.
- `evidence-context-optimization`: Auditable exact-evidence packing, bounded cheap
  selection, expansion/fallback, protected Judge independence and compact
  Architect handoff, with measured cost and coverage gates.

### Modified Capabilities

None. Existing `execution-lifecycle`, `parallel-tdd` and `architect-execution`
requirements continue to govern recovery, immutable evidence and human acceptance.
This proposal adds host capabilities without weakening their requirements.

## Impact

Implementation is limited to the isolated rehearsal host and new host-local
provider/context helpers and offline tests. Existing extension points are
`ModelClient`, `ModelCalls`, `ModelCodingWorkers`, `ContextWorkers`, the Codex
policy constructor and trusted operational recovery. The OpenSpec planning store
is the enclosing checkout; implementation belongs to the existing isolated
backend branch, with a clean saved checkpoint before edits.

No new Python dependency is planned. A tokenizer dependency, if needed for exact
local estimates, requires a separate justified dependency decision; the initial
design supports declared conservative estimates plus authoritative API usage.
No graph/coordinator runtime, shared provider implementation, runtime contract
schema, trusted overlay, lobby product source, frozen test or previous-run changes.
No mainline commit, push, merge, automatic human approval or budget increase.

Acceptance includes direct endpoint/model/effort fidelity, preserved durable
accounting and candidate identity, zero mandatory-evidence omissions, adversarial
selection rejection, correct fallback/recovery, and measured lower Judge input
with no wrong routing on the adjudicated pilot corpus. Target reduction is a
benchmark goal, not authority to discard evidence. The exact rollout gates are
specified in design and delta specs. No settled decision needs superseding:
arbitrary semantic summarization would conflict with D-12 and is excluded.
