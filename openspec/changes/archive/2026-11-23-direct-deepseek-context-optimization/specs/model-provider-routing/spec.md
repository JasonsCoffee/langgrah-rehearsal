# Model provider routing

## Purpose

Allow explicitly configured mixed model backends to serve coding and independent
review while preserving secrets, paid-call identity and the retained run's history.

## ADDED Requirements

### Requirement: All coding stages use the configured direct provider
The host SHALL route every Coder stage and format repair to direct DeepSeek Flash with thinking enabled and low reasoning effort. It MUST NOT route through OpenRouter or silently fall back to Codex, another model or higher effort. The selected endpoint, API model, returned model and policy SHALL be auditable without exposing credentials.

#### Scenario: Any Coder role starts work
- **WHEN** test authoring, implementation, refactoring or a format retry is dispatched
- **THEN** the request uses the approved direct DeepSeek endpoint, Flash model and explicit low thinking policy
- **AND** the same ownership and frozen-source validation applies to its reply

#### Scenario: The provider changes the returned model
- **WHEN** the response identity is outside the approved API-name/version mapping
- **THEN** its usage remains charged and its patch is not admitted until the mismatch is reconciled

### Requirement: Judge configuration remains independent and explicit
The host SHALL use GPT-6.1 Sol with low effort for all future Judge calls, retaining its approved Codex backend, fresh independent context and provider-controlled temperature. Judge MUST NOT receive Coder explanations, private reasoning or authorship signals. Failed review SHALL NOT trigger model or effort substitution.

#### Scenario: Review after backend migration
- **WHEN** a test-validity or defect-routing review begins
- **THEN** it uses the approved GPT-6.1 Sol low policy and source/evidence-only input
- **AND** previous medium-effort receipts remain historical evidence rather than new low-effort approvals

### Requirement: Keys remain local and destination constrained
Direct-provider credentials SHALL be resolved from an explicit local secret reference and excluded from tracked files, exports, prompts and logs. The host MUST reject redirects, unapproved destination hosts and credential-bearing URLs. Missing credentials SHALL block direct dispatch without using another provider.

#### Scenario: No key is available
- **WHEN** the configured local key reference cannot be resolved
- **THEN** preflight reports the missing reference without printing its value or contacting another endpoint

#### Scenario: Endpoint redirects
- **WHEN** the provider response redirects to another destination
- **THEN** the host refuses credential forwarding and records a sanitized operational failure

### Requirement: Direct calls have complete durable accounting
Every direct call SHALL reserve against the existing run before dispatch and reconcile valid provider-reported input and output afterward, including failed or truncated responses. Unknown usage MUST retain its entire reservation. Cached input and reasoning usage SHALL be reported when supplied without subtracting them from aggregate token consumption or counting them twice.

#### Scenario: A response is truncated
- **WHEN** the provider reports usage but completion is incomplete
- **THEN** the usage is charged and the incomplete proposal is rejected
- **AND** any authorized format recovery has a new identity and its own reservation

#### Scenario: A connection ends after possible submission
- **WHEN** no valid usage receipt establishes whether the call was billed
- **THEN** its reservation remains and no automatic replay occurs

### Requirement: Backend migration preserves the current run
Activation SHALL reconcile the current operational boundary, live worker state and all uncertain effects before changing future role policies. It MUST preserve run ID, candidate, contract, budget limits, historical charges, reservations, repair history, frozen files and trusted overlay. Changed policy calls SHALL receive fresh identities; no historical receipt or claim SHALL be rewritten.

#### Scenario: An unresolved old Judge call exists
- **WHEN** activation finds an old claimed call without a complete receipt
- **THEN** it retains and registers the full uncertain charge before public native recovery
- **AND** any new review uses a fresh call identity with the new effort policy

#### Scenario: A worker is still active
- **WHEN** the migration observes a live owner or ambiguous external effect
- **THEN** it waits or reports reconciliation required instead of reclaiming locks or dispatching a duplicate operation

### Requirement: Existing stage limits remain visible
The host SHALL retain approved aggregate limits and make each role's output allocation, actual usage and remaining totals observable. Switching providers MUST NOT create an unrecorded hard input ceiling, silently clamp a stage allocation, erase historical effort overrides or reset counters. The current all-Coder low decision SHALL explicitly supersede earlier per-unit effort exceptions for future calls only.

#### Scenario: A request exceeds provider capacity
- **WHEN** exact required input or output cannot fit the selected provider's verified limits
- **THEN** the host reports the capacity blocker before dispatch where knowable and preserves all required evidence
- **AND** it does not silently truncate, substitute a model or increase the run budget

### Requirement: Activation requires verified policy and preserves review gates
The role migration SHALL remain inactive until offline checks, credential/model preflight and a bounded candidate-bound pilot establish the requested routes, efforts and receipt accounting. After activation the run SHALL retain sequential verification and independent judging, and end at awaiting_human_review only after real acceptance gates pass.

#### Scenario: Provider pilot succeeds but tests have not passed
- **WHEN** the pilot proves direct access and low-effort Judge availability
- **THEN** migration readiness is recorded separately from game completion
- **AND** no accepted pass or human approval is manufactured
