# evidence-context-optimization Specification

## Purpose

Reduce avoidable model input through verifiable source selection and compact
handoffs while preserving the information and independence required for review.

## Requirements

### Requirement: Each review has a canonical evidence identity
The host SHALL retain an immutable, secret-filtered canonical packet and a content-addressed inventory for each review. The inventory MUST bind run, contract, candidate, unit, stage, source bytes, policy and evidence identities. Every optimized packet SHALL identify its canonical parent and record included, deduplicated and omitted items with reasons.

#### Scenario: A candidate changes after selection
- **WHEN** source, contract, test hashes, evidence or role policy differs from the selection manifest
- **THEN** the previous optimized packet is invalid for the new review and cannot reuse its verdict

### Requirement: Required Judge evidence cannot be reduced semantically
Judge input SHALL preserve exact applicable criteria and spec clauses, ownership, full current patched files, mechanical gate and diagnostics, failing test identities, assertions and required related test/helper/dependency source. Test-validity reviews SHALL retain the complete reviewed tests and required fixtures. Mandatory items MUST be included regardless of selector output; uncertain dependencies SHALL trigger expansion or full context.

#### Scenario: Selection omits a failure or patched file
- **WHEN** a proposed selection lacks a required item
- **THEN** the host restores that exact item or rejects the selection before Judge dispatch
- **AND** it does not replace it with a summary or a hash alone

#### Scenario: A required peer dependency is unresolved
- **WHEN** exact source dependencies cannot be established sufficiently for the review
- **THEN** the host includes the complete implicated context or stops for a capacity blocker

### Requirement: The optimizer receives no Coder self-assessment
All Judge-bound optimization SHALL begin from independently assembled source and mechanical evidence. Coder reasons, private reasoning, identity and self-assessment MUST be removed before the cheap selector receives input. Selector output SHALL NOT supply classifications, confidence, recommended verdicts or natural-language evidence in the authoritative Judge packet.

#### Scenario: Coder notes claim a repair is complete
- **WHEN** the worker response includes completion claims or explanations
- **THEN** those fields are excluded from both the selector and Judge input
- **AND** actual source and verification evidence remain the basis of review

### Requirement: Cheap selection is constrained to exact references
The optional DeepSeek selector SHALL return only validated references to supplied source items and permitted exact spans, with coverage identifiers. The host MUST hydrate the bytes itself, reject unknown identities, ambiguous ranges, changed hashes and unauthorized exclusions, and prohibit selector file, network or state access. Instructions inside supplied source SHALL be treated as data.

#### Scenario: Source text instructs the selector to hide a defect
- **WHEN** embedded text requests removal of a failure, ownership rule or test
- **THEN** it cannot change the mandatory set or introduce instructions into the Judge packet

#### Scenario: The selector invents an excerpt
- **WHEN** an output span does not match the identified canonical source bytes
- **THEN** that selection is rejected and no invented evidence reaches Judge

### Requirement: Deterministic packing precedes paid reduction
The adapter SHALL first remove duplicate representations and irrelevant metadata without changing source semantics. It MUST retain source provenance, distinct failure identities and meaningful multiplicity. Paid selection SHALL be bypassed for small packets, absent optional content, exact cached selections or insufficient expected benefit.

#### Scenario: The same evidence is serialized twice
- **WHEN** identical content appears in several eligible input slots
- **THEN** it is supplied once with references preserving all required relationships
- **AND** distinct tests or failure occurrences are not merged merely because their messages match

### Requirement: Expansion and fallback are bounded and auditable
Judge SHALL be able to request additional exact context through a host-controlled bounded protocol before final classification. Unknown scope, invalid selection, insufficient savings or unresolved omissions SHALL fall back to the full admissible canonical packet when it fits. The host MUST stop rather than silently truncate required context, repeat uncertain calls or accept a verdict from an incomplete packet.

#### Scenario: Judge requests another helper
- **WHEN** a valid context request identifies an available canonical helper
- **THEN** the host supplies its exact bytes under a new paid identity while retaining candidate and evidence provenance
- **AND** a context request is not interpreted as an implementation or contract verdict

#### Scenario: The required packet cannot fit
- **WHEN** the complete mandatory input exceeds verified model capacity
- **THEN** the host records the exact capacity blocker and retains state without weakening evidence or substituting a model

### Requirement: Optimizer calls share the existing budget and recovery rules
Selector, expansion and comparison calls SHALL reserve and settle through the same persistent run ledger as Coder and Judge. They MUST use distinct auditable purpose identities without adding contract coding units. Unknown usage SHALL remain reserved; an uncertain selector call SHALL stop for reconciliation before any fallback dispatch.

#### Scenario: Selector fails after submission
- **WHEN** completion and usage are unknown
- **THEN** its full reservation remains and no automatic full-context Judge call is dispatched

### Requirement: Architect handoff retains original authority
Judge–Architect handoff SHALL carry the exact per-unit classification and explanation, unresolved findings, candidate/contract identities, budget state and direct references to immutable originals. Repeated supporting context SHALL be replaced by verified references and compact indexes. A generated digest MUST NOT alter scope, settle conflicts, drop uncertainty or replace the original verdict, dossier or human decision.

#### Scenario: A compact handoff omits an unresolved finding
- **WHEN** the handoff inventory fails to account for every unresolved finding
- **THEN** the host rejects it or includes the full original handoff

#### Scenario: The Architect cannot resolve a reference
- **WHEN** the recipient lacks access to a referenced source
- **THEN** that exact necessary source is hydrated inline or the handoff is reported incomplete

### Requirement: Optimization is qualified by quality and net benefit
Before active reduction, the host SHALL compare canonical and optimized review on a frozen adjudicated corpus with the same Judge model/effort. Qualification MUST show zero missing mandatory items, no incorrect adjudicated routing and a measured input reduction. Reports SHALL separate selector overhead, Judge input/output, cache usage, latency and total monetary cost; unknown prices or tokenizer estimates MUST be labeled.

#### Scenario: Compression lowers Judge input but increases total cost
- **WHEN** selector overhead and expansion exceed the measured saving
- **THEN** paid selection is not enabled for that packet class and deterministic packing remains available

#### Scenario: The two Judge runs disagree
- **WHEN** optimized and canonical judgments disagree or coverage is challenged
- **THEN** the packet class fails qualification pending adjudication; agreement alone is not proof of correctness

### Requirement: Reuse and rollback preserve correctness
Selection and review reuse SHALL require exact source, candidate, evidence, schema, role and effort policy identities. Disabling optimization SHALL restore canonical future input without modifying historical receipts, usage, source, tests or review state. No compaction result SHALL approve human review or weaken sequential verification.

#### Scenario: Judge effort changes from medium to low
- **WHEN** prior review receipts use a different effort policy
- **THEN** they remain inspectable but cannot masquerade as a review dispatched under the new low policy

#### Scenario: Rollout detects an omission
- **WHEN** an active packet fails completeness checks
- **THEN** the adapter is disabled for that class and affected decisions require complete-evidence review with new identities

### Requirement: Optimizer returns input and check results together
The context optimizer SHALL return optimized input, structured check results and a delivery decision for every invocation, including bypass and failure paths. Checks MUST distinguish code-verified facts from model-reported claims and include completeness, integrity, dependencies, filtering, identity, savings and budget. Failed or unknown correctness checks SHALL prohibit optimized delivery.

#### Scenario: Optimization succeeds
- **WHEN** the adapter validates the selected exact context and qualifies its use
- **THEN** it returns the optimized packet, evidence-backed check results, size/cost metrics and `use_optimized` together
- **AND** the Host verifies that result identity before downstream dispatch

#### Scenario: A check is unknown or fails
- **WHEN** a required correctness check cannot establish safe optimized delivery
- **THEN** the adapter returns failed or unknown checks and the reason, with `use_original` and exact original input if safe, otherwise `blocked`
- **AND** a model-reported pass alone cannot authorize delivery
