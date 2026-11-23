# Brainstorm

## Outcome and acceptance criteria

Reduce the retained lobby run's model cost and repeated input while preserving
evidence quality, independent judgment, frozen tests and recovery guarantees.
This is a planning-only proposal for host/backend composition, not execution or
game implementation. The governing boundaries are `docs/boundary-contract.md`
(Judge inputs and bias control), `docs/loop-control.md` (paid identity and retained
usage), `docs/verification.md` (truth and provenance), `docs/adapters.md`, and
settled decisions D-12 and D-28. Existing framework runtime remains outside scope.

Success means all Coder stages use direct DeepSeek Flash with explicit low
reasoning, Judge uses GPT-6.1 Sol with explicit low reasoning, and a separately
accounted DeepSeek context selector reduces avoidable Judge input. No decision
relies on a summary in place of required evidence. Candidate, contract, ledgers,
reservations and test hashes survive activation unchanged. Optimization must show
measured net benefit and retain complete traceability, rather than promise a
fixed reduction that might require omitting necessary context.

## Current evidence and constraints

- The active execution code is in the isolated `codex/codex-worker-backend`
  checkout; the enclosing framework checkout is the existing planning store.
  Do not initialize another store or mutate previous-run artifacts to implement
  this proposal. The new planning change is distinct from the lobby product plan.
- `ModelClient` currently builds OpenRouter-specific request fields and its TOML
  loader rejects other provider types. Changing the URL/key alone is insufficient.
  A host-local direct client can implement the existing client interface without
  changing coordinator, graph, contract schema or shared provider runtime.
- The lobby host currently selects both clients together. Several context, review
  reuse, frozen-source, receipt and error helpers assume both are Codex or hardcode
  Judge medium effort. Mixed-backend activation requires explicit wiring changes,
  policy-specific validation and new call IDs, not a global text replacement.
- Current and historical host prompts duplicate spec text, full read-only suites,
  retained implementations, previous diagnostics and repair instructions. Paid
  prompts were often around one megabyte. Redundant input is a credible target,
  but this observation does not prove every byte is dispensable.
- The durable run is `monopoly-game-lobby`, contract version 70 and hash
  `bbbfcf9dc2b51f1ffb9d8a935a1fbb72ca148ada5c2a89f6b37752065f9315e7`.
  Its last observed result is operational at candidate
  `625db77bf4e75060435947d955328a729f6f87dc`, not human review. The current
  status reports 160,700,047 input / 6,517,038 output; limits remain 250,000,000
  input / 24,000,000 output / 160 cycles, added-unit bound 2. These are snapshots,
  not permission to overwrite live state; activation must re-read the ledger.
- The complete 199-file test/configuration inventory SHA256 is
  `2da65db6815d61fb277a19f826b4d512e78c8bc4dc2f4f8c4d1b3387e8d1c520`.
  The last verified uncertain set contained 26 reservations; a subsequent stop
  may add another. Reconcile the complete live set, never assume a fixed count.
- No direct DeepSeek endpoint or process `DEEPSEEK_API_KEY` was found. This
  proposal does not solicit secrets in chat, copy Codex credentials or invoke a
  paid API call. Actual key/model availability remains an activation prerequisite.

## Alternatives and trade-offs

1. Change only endpoint/key: rejected. OpenRouter parameter dialect, role coupling,
   receipt assumptions and changed model identity remain unresolved.
2. Let a cheap model rewrite the whole Judge prompt: rejected. Rewriting code,
   evidence or requirements can silently alter meaning; sharing a model with Coder
   can bias omissions. It cannot guarantee all important information survives.
3. Deterministic canonical packing first, optional model-assisted selection of
   exact spans second: chosen. A trusted manifest defines nonremovable facts;
   the selector has no verdict authority and cannot paraphrase evidence. Exact
   source hydration, completeness guards and full-context fallback preserve the
   existing Judge boundary. Savings are workload-dependent.
4. Summarize every Judge reply with another paid call: rejected as a default.
   Replies are often already short and a second call may cost more. Deterministic
   indexing and reference-based handoff are the default; cheap selection applies
   only to sufficiently large redundant supporting context.
5. Rewrite framework runtime now: deferred. Prove a portable host-local extension
   against the real rehearsal; promote a generic capability in a separately
   reviewed framework change if justified.

## Decisions and assumptions

**Explicit user decisions:** direct DeepSeek Flash / low reasoning for every
Coder role, GPT-6.1 Judge / low reasoning, a cheaper-model input optimization
adapter, consideration of Judge–Architect trimming, a complete proposal, and
preservation of the same run, usage, reservations, budgets, trusted overlay and
frozen tests. The existing Judge identity is GPT-6.1 Sol, so that exact model is
retained; only its reasoning effort changes.

**Proposed implementation defaults, not already activated:** API name
`deepseek-flash`; context selector also uses direct Flash / low in a separate
request; host-local extensions; exact evidence selection rather than rewritten
source; stable canonical prefixes; one selector attempt per input hash; bounded
Judge requests for additional exact context; full-context fallback when validation
or savings checks fail. Details and rollout thresholds are in design/specs.

**Provider facts checked on 2026-11-23:** the official pricing page maps
`deepseek-flash` to DeepSeek-V4.1-Flash-1017; thinking mode supports explicit low
effort and ignores temperature. This means low must be sent explicitly, rather
than relying on the provider's high default. Cache hits reduce money, not the
ledger's recorded input consumption. Model-version mapping is reverified at pilot.

## Open questions

No product-scope question blocks the proposal. Implementation must verify the
local key, returned model identity and low-effort support, reconcile the newest
operational stop, and benchmark exact tokenizer/cost information available for the
selected Judge route. These are specific activation gates. Unknown dollar prices
must remain unknown rather than be estimated as verified savings. This proposal
does not authorize live dispatch or an aggregate budget increase.

References: [DeepSeek models/pricing](https://api-docs.deepseek.com/quick_start/pricing/),
[thinking controls](https://api-docs.deepseek.com/guides/thinking_mode/),
[prefix caching](https://api-docs.deepseek.com/guides/kv_cache/).

User refinement confirmed: the context optimizer returns both optimized input and
structured optimization-check results. Host means the trusted execution program;
the optimizer adapter includes model selection and deterministic verification.
