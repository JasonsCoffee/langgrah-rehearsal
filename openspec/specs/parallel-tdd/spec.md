# parallel-tdd Specification

## Purpose

Enforce independently tested Red-Green-Refactor work for isolated coding units
while producing trustworthy evidence from sequential integrated verification.

## Requirements

### Requirement: Tests are independently authored and validated before freeze
Test-role units SHALL author tests from declared spec scenarios before implementation dispatch. Coverage and validity review SHALL establish scenario mappings, intended assertions, discovery expectations, and baseline outcomes. Test files SHALL freeze before any implementation unit runs and remain immutable for the cycle.

#### Scenario: Implementer weakens its acceptance tests
- **WHEN** an implementation patch modifies a frozen test, test configuration, or declared acceptance selection
- **THEN** integration rejects the patch instead of repairing or accepting the modified test

#### Scenario: Test author produces invalid setup
- **WHEN** baseline execution fails because of invalid test setup or an unrelated structural error
- **THEN** the failure does not qualify as Red and test preparation is corrected before freeze

#### Scenario: A frozen test is later found defective
- **WHEN** evidence shows a frozen test contradicts its spec or cannot execute correctly
- **THEN** it returns as a contract defect for a revised version rather than being edited by an implementation unit

### Requirement: Red is evidenced against a known baseline
Every active implementation unit SHALL have baseline evidence for its mapped acceptance behavior before Green work. Expected assertion failures SHALL count as Red; tooling failures and syntax errors SHALL NOT. Already-passing behavior SHALL require an explicit coverage review and recorded exception rather than artificial breakage.

#### Scenario: New component API is required
- **WHEN** tests depend on a new API
- **THEN** the Architect supplies a compilable shell before baseline tests so Red can demonstrate missing behavior

#### Scenario: Behavior already satisfies the specification
- **WHEN** the baseline passes the mapped tests
- **THEN** coverage is reviewed and the unit records an already-satisfied result or receives revised coverage before implementation proceeds

### Requirement: Green and Refactor require verification
Each unit SHALL make the required behavior pass before refactoring and retain the verified Green snapshot. Refactor SHALL preserve tests, ownership, and frozen interfaces and require new passing evidence. A reasoned no-change refactor decision SHALL be valid. Refactor failure SHALL restore Green before bounded repair.

#### Scenario: Cleanup breaks behavior
- **WHEN** a refactor candidate fails verification
- **THEN** the unit returns to its verified Green snapshot and the failure is recorded without declaring completion

### Requirement: Coding work is isolated
Coding units SHALL produce changes in separate workspaces based on identified revisions. They SHALL NOT mutate shared integration, verification, frozen inputs, or another unit's workspace. Worktree separation SHALL be supplemented by enforceable command and filesystem restrictions.

#### Scenario: Agent attempts to edit a neighboring unit
- **WHEN** a coding tool targets another workspace or shared repository metadata
- **THEN** the execution boundary denies that operation and records the violation

### Requirement: Coordinator integrates candidates sequentially
Only the coordinator SHALL apply unit candidates to integration state after ownership, baseline, and dependency validation. Candidate evidence SHALL identify its base revision and dependency revisions. Stale candidates SHALL be refreshed and reverified when affected inputs change.

#### Scenario: Dependency changes after unit coding starts
- **WHEN** a unit submits work based on an older revision of a declared dependency
- **THEN** its result is not accepted as current Green without validation against the updated dependency

### Requirement: Unity verification is sequential and blocking
The Unity adapter SHALL execute at most one EditMode verification at a time per verification project. Each call SHALL block until a result or operational failure is available. Other independent coding units SHALL be able to continue working during that call.

#### Scenario: Two candidates await EditMode tests
- **WHEN** one candidate is already being tested and another becomes ready
- **THEN** the coordinator schedules the second after the first completes without concurrent Unity access to that project

### Requirement: Evidence describes immutable verification inputs
Verification SHALL run against an identified snapshot that cannot change while any gate executes. The ladder SHALL run ownership, parse/conformance, compile, then tests and stop at the first failure. Evidence SHALL include snapshot, selected tests, discovered/executed counts, results, and relevant environment identity.

#### Scenario: Another patch arrives during testing
- **WHEN** verification is running and another coding unit submits a patch
- **THEN** that patch does not alter the snapshot under test

#### Scenario: Compile gate fails
- **WHEN** compilation fails for the candidate
- **THEN** behavioral tests do not run and the failure retains its structural gate classification

### Requirement: Test execution cannot silently yield a false pass
Verification SHALL reject absent required tests, zero discovered or executed tests, unexpected skips, inconclusive outcomes, and stale result artifacts. A focused passing test run SHALL NOT substitute for the full integrated EditMode acceptance suite.

#### Scenario: Filter matches no tests
- **WHEN** the requested unit test selection executes no tests
- **THEN** the unit is not marked Green

#### Scenario: All units pass focused tests
- **WHEN** all unit candidates have passing focused evidence
- **THEN** the final integrated revision still requires the full required EditMode suite before human review

### Requirement: Integration evidence can implicate multiple units
Failure evidence SHALL distinguish test authors, implementing units, and observed candidate changes. A shared failure SHALL retain the involved unit set and SHALL NOT be assigned from file path or test name alone. Proposed coordinated repairs SHALL stay within each participant's ownership and budget.

#### Scenario: Shared behavior fails after individually passing changes
- **WHEN** a shared acceptance test fails only in the integrated candidate
- **THEN** the coordinator records an integration failure linked to all relevant units and obtains evidence-based routing
- **AND** unresolved scope or interface ambiguity escalates to the Architect rather than permitting ownership changes

### Requirement: Retry policy is deterministic and bounded
Expected Red SHALL NOT count as a failed implementation attempt. STALLED SHALL escalate immediately. The first REGRESSED failure SHALL restore the affected snapshot and permit one retry within the attempt budget; a second regression or failed-attempt exhaustion SHALL escalate as contract regardless of judge output. TDD stages and attempt trends SHALL be recorded separately.

#### Scenario: Judge requests unlimited implementation repair
- **WHEN** the unit exhausts its permitted failed implementation attempts
- **THEN** the coordinator escalates it as a contract defect even if the judge continues to classify implementation

#### Scenario: Refactor repeatedly regresses
- **WHEN** a second regression occurs across the unit's Green and Refactor repair history
- **THEN** the coordinator restores safe state and escalates without resetting the budget at the stage transition

### Requirement: Coding worktrees stay outside Unity import
All preparation, coding-unit, and integration checkouts SHALL be located outside Unity-imported directories. A nested game repository SHALL NOT cause its external worktrees to be imported as extra copies. Coding agents SHALL NOT require a running Unity editor or direct editor-control access in their worktrees.

#### Scenario: Unsafe worktree location is configured
- **WHEN** a coding or integration checkout would be placed beneath a verification project's imported Assets tree
- **THEN** workspace preflight rejects the location before creating or importing a duplicate game assembly or asset set

### Requirement: Verification materializes exactly one game candidate
The verification worker SHALL use a complete dedicated Unity host with identified shared dependency revisions and exactly one candidate game module. It SHALL materialize the requested game revision only at the authorized mount, preserve tracked metadata, remove stale prior-candidate content safely, and lock the materialized state before gates execute.

#### Scenario: Nested game worktree lacks the Unity host
- **WHEN** a module-only worktree is submitted for Unity verification
- **THEN** the worker uses the complete configured host rather than treating the worktree as a standalone Unity project

#### Scenario: Candidate deletes an asset
- **WHEN** the next candidate no longer contains an asset from the previous managed candidate
- **THEN** materialization removes only that stale managed content and its corresponding metadata before validating the new manifest

#### Scenario: Host dependencies drift
- **WHEN** shared modules, packages, or project settings differ from the required host profile
- **THEN** verification reports an operational baseline mismatch and does not accept results as evidence for the requested candidate

### Requirement: Shared host integrity survives verification
Verification SHALL preserve shared source, assets, package configuration, and project settings. Expected caches, logs, and approved worker evidence SHALL be confined to configured operational locations in the dedicated environment. Such outputs SHALL NOT authorize host source changes or enter the delivered game patch.

#### Scenario: Import callback changes shared settings
- **WHEN** candidate import or a verification command changes protected host content
- **THEN** the worker rejects the contaminated result, retains diagnostics, and stops for controlled reconciliation without modifying the user's interactive project
