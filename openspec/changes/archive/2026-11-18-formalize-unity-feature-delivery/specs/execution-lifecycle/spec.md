# Execution Lifecycle Spec Delta

## Purpose

Expose reliable execution progress and recoverable outcomes while ensuring only
the exact human-accepted candidate can complete the delivery lifecycle.

## ADDED Requirements

### Requirement: Architect can observe execution without controlling it
The coordinator SHALL publish an atomically replaced status snapshot and ordered progress records under .agent/runs/<run_id>/. Records SHALL identify run, contract, sequence, time, per-unit stage/state, attempts, and active verification snapshot. Heartbeats SHALL distinguish activity from stale status without implying success.

#### Scenario: Parallel units occupy different stages
- **WHEN** one unit is coding, another waits for verification, and another is refactoring
- **THEN** status reports all three independently instead of presenting a misleading single TDD stage

#### Scenario: Progress stops arriving
- **WHEN** a heartbeat becomes stale
- **THEN** the Architect treats the status as unknown or interrupted rather than accepted completion

### Requirement: Recovery reconciles durable execution effects
The coordinator SHALL persist operation identity and inputs before applying patches or starting verification. Recovery SHALL reconcile filesystem state, operation records, locks, and checkpoint state before resuming. It SHALL NOT duplicate patch application, reuse mismatched evidence, or blindly clear locks held by live processes.

#### Scenario: Crash after patch application
- **WHEN** execution restarts after a patch was applied but before its completion record was written
- **THEN** recovery recognizes or restores that application before proceeding instead of applying it again

#### Scenario: Crash while Unity is still running
- **WHEN** a coordinator restarts while its prior verifier process may remain active
- **THEN** it reconciles process ownership and waits or performs controlled cleanup before another verification starts

### Requirement: Budgets survive revisions and recovery
Model usage, failed attempts, regressions, and cycle consumption SHALL remain durable across restart, human review, and ownership migration. Exhaustion SHALL stop further paid dispatch, restore safe state, and emit abandon evidence. Unknown usage after interruption SHALL be conservatively reserved or reconciled before more model calls.

#### Scenario: Unit is split after failed attempts
- **WHEN** the Architect replaces a unit with multiple units in the next contract version
- **THEN** run-level consumed resources and relevant repair history are retained rather than reset

### Requirement: Operational abort and cancellation preserve work
Operational failure and cancellation SHALL terminate execution without manufacturing unit defects. The coordinator SHALL stop or reconcile active workers, retain inspectable candidates and evidence, release only owned locks, and preserve the starting user workspace. Verification unavailability SHALL NOT consume a unit attempt or contract cycle.

#### Scenario: User cancels while a model or Unity process is active
- **WHEN** cancellation is requested
- **THEN** execution stops new dispatch, reconciles active operations, and records cancelled outcome with retained work references

#### Scenario: Tooling fails after integration has begun
- **WHEN** a later gate cannot run
- **THEN** partial agent work remains inspectable in managed workspaces while the user's starting workspace remains untouched

### Requirement: Automated success waits for human acceptance
A fully verified candidate SHALL enter awaiting_human_review instead of accepted pass. The review package SHALL identify contract/hash, candidate revision, presentation baseline, verification evidence, launch instructions, required interactions, visual references, and placeholder limitations.

#### Scenario: EditMode suite is green
- **WHEN** all automated acceptance gates pass
- **THEN** execution prepares a reviewable candidate and waits without flushing final constraints or claiming full task completion

### Requirement: Human approval is revision-specific
Only explicit human approval of the identified review candidate SHALL permit accepted pass. Approval SHALL record reviewer identity, decision, reviewed revision, and evidence references. Any change to the candidate's relevant source, tests, assets, bindings, configuration, or requirements SHALL invalidate approval.

#### Scenario: Candidate changes after approval
- **WHEN** a newer source or presentation revision replaces the approved candidate
- **THEN** the old approval cannot complete the new candidate

### Requirement: Review feedback follows the correct repair boundary
Human findings SHALL distinguish implementation violations, contract/presentation changes, and excluded placeholder polish. Implementation-only repair SHALL remain under the frozen contract if feasible; requirement or presentation revision SHALL return to the Architect. Every repaired candidate SHALL be reverified and reviewed within the retained run budget.

#### Scenario: Button violates an existing requirement
- **WHEN** the human finds a broken interaction already specified by the contract
- **THEN** the repair routes to the responsible implementation units without automatically relabeling it a contract defect

#### Scenario: Human requests another layout
- **WHEN** feedback requires changing a frozen layout or binding
- **THEN** execution returns the finding for Architect revision and a new contract version

#### Scenario: Candidate is not runnable
- **WHEN** automated execution ends with failed compilation or unresolved contract defects
- **THEN** it emits its normal failure result rather than requiring an impossible visual review

### Requirement: Accepted completion preserves provenance
After human approval the Architect SHALL perform planning-level reconciliation before archive. Only accepted completion SHALL flush provenance-backed learned constraints into the managed AGENTS.md block, preserving unrelated content and the existing deduplication/archive policy. Execution SHALL never push or merge into mainline automatically.

#### Scenario: Rejected candidate learned a possible constraint
- **WHEN** a candidate lacks human acceptance
- **THEN** its learned statements remain evidence or hypotheses rather than final managed constraints

### Requirement: Framework verification remains offline
Framework acceptance tests SHALL exercise lifecycle, presentation protection, scheduling, and repair with fake agents/adapters/transports and no network or Unity installation. Real Unity validation SHALL be a separately identified integration milestone, not a prerequisite for the framework test suite.

#### Scenario: Developer runs the framework suite without Unity
- **WHEN** offline acceptance checks execute
- **THEN** no provider key, network service, Unity installation, or game project is required

### Requirement: Verification requests are independent of editor-control transport
Each request SHALL identify run, contract/hash, candidate, presentation baseline, coding profile, host profile, test selection, and request ID. The worker SHALL correlate all completion evidence to those inputs. Editor-control polling SHALL remain internal to a blocking verification call and SHALL NOT replace it with event-driven graph execution.

#### Scenario: Worker receives an unrelated result file
- **WHEN** a prior test report has a different request ID or candidate identity
- **THEN** the worker rejects it rather than returning a pass for the current request

### Requirement: Editor identity and reload recovery are verified
Before editor operations the worker SHALL validate health and exact target project identity using bounded endpoint discovery. After refresh or Domain Reload it SHALL rediscover identity and reconcile request state. Unreachable or mismatched editor instances SHALL produce operational failure rather than unit blame or unapproved editor/package installation.

#### Scenario: Another editor answers at the expected port
- **WHEN** the endpoint is healthy but reports another project
- **THEN** the worker refuses to operate on that editor

#### Scenario: Domain Reload loses in-memory task state
- **WHEN** the editor restarts its Bridge and the previous task ID disappears
- **THEN** the worker checks durable request evidence and editor state before deciding whether a safe retry is possible

### Requirement: Editor commands cannot imply test success
The worker SHALL distinguish command submission, nested command outcome, compilation readiness, test completion, and test pass. Durable completion evidence SHALL include discovery/execution results and request provenance. A successful menu invocation or Bridge task SHALL NOT alone satisfy any acceptance gate.

#### Scenario: Menu command returns before test callbacks finish
- **WHEN** the editor reports that a test menu command executed successfully
- **THEN** the worker continues waiting for the matching test completion evidence within a bounded timeout

#### Scenario: Bridge task succeeds with an inner error
- **WHEN** the transport reports task success but its command result reports an error
- **THEN** the worker handles that error and does not mark the test stage passed

### Requirement: Editor control remains worker-scoped
Only authorized preparation tooling or the verification worker SHALL access editor mutation commands for its assigned workspace. Coding units SHALL NOT receive broad Bridge/menu access. Missing test capabilities SHALL be added through owned game-local editor/test integration rather than modifying shared Bridge/package source.

#### Scenario: Unit attempts arbitrary editor actions
- **WHEN** a coding unit requests scene modification or a host-wide generation menu through the Bridge
- **THEN** the execution boundary rejects the action instead of forwarding unrestricted editor control
