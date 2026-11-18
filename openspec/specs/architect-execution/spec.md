# architect-execution Specification

## Purpose

Define the boundary through which Codex with OpenSpec delegates planned work to
the executor while retaining authority over scope, contracts, and acceptance.

## Requirements

### Requirement: Delegated apply preserves planning authority
The Architect SHALL translate ready OpenSpec planning artifacts into an executable contract. The executor SHALL NOT edit planning artifacts or mark their tasks complete. Planning verification, synchronization, and archive SHALL remain Architect responsibilities.

#### Scenario: Task completion is reconciled
- **WHEN** execution delivers accepted evidence for every unit and criterion mapped to an OpenSpec task
- **THEN** the Architect can mark that task complete using the evidence
- **AND** partially delivered tasks remain incomplete

### Requirement: Versioned runtime boundary
The Architect SHALL publish contracts at specs/<NNN-feature>/contract.v<N>.json beside spec.md and invoke the executor with the contract path and run ID. The executor SHALL validate fixed contract bytes and record their hash. contract_version SHALL be the cycle number, separate from format compatibility metadata.

#### Scenario: Contract changes during execution
- **WHEN** the referenced contract bytes change after validation
- **THEN** the executor rejects further application under the changed contract instead of silently adopting it

#### Scenario: Contract defects return to planning
- **WHEN** contract rework is required
- **THEN** the executor records a dossier at .agent/runs/<run_id>/dossier-v<N>.json and ends that invocation
- **AND** the Architect revises planning and invokes the next version using the same run ID

### Requirement: Fixed units and validated ownership
The executor MUST reject duplicate IDs, invalid dependencies, empty ownership, ownership collisions, forbidden paths, and unsupported contract formats. Unit membership and ownership SHALL remain immutable within a cycle. Path comparison and generated-file rules SHALL come from the selected adapter.

#### Scenario: Scope cannot be expanded by a coder
- **WHEN** a unit needs an unowned file, a frozen file, or a new contract unit
- **THEN** execution reports the scope problem instead of creating units or changing ownership

#### Scenario: Invalid dependency graph
- **WHEN** a contract contains a missing dependency, a dependency cycle, or a test unit that requires implementation before test freeze
- **THEN** validation rejects the contract before dispatch

#### Scenario: Paths remain confined
- **WHEN** ownership resolves outside the target tree, through a link to protected space, or into the runtime specs tree
- **THEN** validation rejects that ownership before any write

### Requirement: Explicit task and test relationships
Contracts SHALL map stable OpenSpec task references to units and criteria, and distinguish each test's author from its implementing units. Shared acceptance tests SHALL support multiple implementing units without implying a unique culprit.

#### Scenario: One task requires multiple units
- **WHEN** a task maps to one test author and two implementation units
- **THEN** completion requires all mapped deliverables and criteria, not the first passing unit

#### Scenario: Shared test fails
- **WHEN** a shared acceptance test fails after integration
- **THEN** evidence retains all related unit IDs and the tested snapshot without assigning blame from its name alone

### Requirement: Architect-controlled ownership migration
Between consecutive versions the Architect SHALL explicitly declare ownership transfers with source, destination, paths, and rationale. Retired units SHALL remain as superseded history. Every current writable path SHALL have exactly one active owner, and migrations SHALL preserve run budgets and history.

#### Scenario: Existing unit is split
- **WHEN** a revised contract supersedes U1 and transfers its two files to U2 and U3
- **THEN** validation accepts only a complete, collision-free migration within approved scope
- **AND** U1 remains in historical records without reserving the transferred files in the current map

#### Scenario: Silent reassignment or removal
- **WHEN** a new version omits a previous unit or changes an existing file's owner without a migration
- **THEN** the executor rejects the revision

### Requirement: Two failure loops and independent judging
Implementation defects SHALL remain inside execution; contract defects SHALL return through a dossier. Classification SHALL be per unit with shared evidence references where needed. Judges MUST use a different model, default to temperature zero unless provider-controlled temperature is explicitly approved under D-28, read criteria, spec, evidence, and patched files, and receive no coder notes or authorship signals. Provider-controlled temperature MUST omit the temperature parameter, preserve configured reasoning effort, and never activate as automatic fallback.

#### Scenario: Mixed defects in one candidate
- **WHEN** evidence supports an implementation defect in one unit and a contract defect in another
- **THEN** the dossier preserves separate unit classifications instead of one global defect class

### Requirement: Structured execution outcomes
Each invocation SHALL persist a machine-readable result with run ID, contract version/hash, outcome, candidate revision where available, and evidence references. Outcomes SHALL distinguish awaiting_human_review, rework, abandon, operational, cancelled, and accepted pass. Logs and progress SHALL NOT establish completion.

#### Scenario: Infrastructure is unavailable
- **WHEN** the verifier cannot run because tooling or access is unavailable
- **THEN** the result reports operational failure without consuming a unit attempt or blaming a coding unit
- **AND** no contract-defect dossier is manufactured

### Requirement: Onboarding establishes a non-expandable game boundary
The target profile SHALL distinguish Unity host root, game repository root, and allowed game mount. Architect preparation and executor changes MUST stay within the authorized game scope. Contracts, ownership migrations, generated-file exemptions, and indirect tool actions SHALL NOT widen that scope.

#### Scenario: Contract claims shared framework code
- **WHEN** a contract or candidate attempts to change a sibling module, host package, project setting, or server repository
- **THEN** preflight or integration rejects the change even if a unit lists that path in owns

#### Scenario: Nested repository uses module-relative ownership
- **WHEN** the game repository is mounted at Assets/JJGame/monopoly in a larger Unity host
- **THEN** Runtime/Script ownership resolves within that game checkout and maps to the same module in verification without granting writes to the host

### Requirement: Architect preserves source provenance and project knowledge
The Architect SHALL reuse existing game OpenSpec planning, design sources, game wiki, framework reference knowledge, and current source. Exported criteria SHALL retain source identities and hashes. Conflicting requirements, summaries, or implementation facts SHALL be surfaced for resolution rather than silently overriding authoritative inputs.

#### Scenario: Wiki and original design disagree
- **WHEN** a wiki summary differs from an original design on an acceptance behavior
- **THEN** the Architect resolves and records the requirement before freezing its contract, retaining references to the relevant sources

### Requirement: Coding restrictions are versioned execution inputs
The Architect SHALL export applicable game/module rules and verified framework API references as a hashed target coding profile. Coding agents SHALL receive the relevant profile; verification SHALL enforce mechanically checkable restrictions. Game-specific constraints SHALL NOT be hardcoded into stack-agnostic core behavior.

#### Scenario: Target uses a hot-update module
- **WHEN** a feature targets the existing game assembly and service lifecycle
- **THEN** its units preserve assembly identity, permitted dependency direction, serialization, resource routing, and teardown rules
- **AND** missing APIs are investigated before implementing duplicate infrastructure
