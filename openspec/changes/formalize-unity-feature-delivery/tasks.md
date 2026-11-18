# Tasks

This is the overall roadmap, not a completed implementation phase. Paths below
are planned destinations for the rebuilt package. Do not reuse the wireframe as
a behavioral spec. Each numbered group depends on the previous group unless a
task explicitly narrows that dependency. Tests for a group are authored, observed
failing for the intended missing behavior, and frozen before that group's runtime
implementation begins. A frozen-test defect returns to planning. All pytest
checks are offline with fake models/adapters/transports; real Unity demonstrations
are separate milestones. No task authorizes a mainline commit, push, or merge.

Framework paths are repository-relative. `GAME_ROOT/` in later deployment tasks
means the authorized game checkout mounted at `Assets/JJGame/monopoly/` inside a
dedicated host; `UNITY_HOST/` means that complete verification environment. They
are configuration tokens, not literal folders to create. The user's interactive
project and shared host source/settings remain unchanged. Deployment tasks require
authorized external locations and confirmed target identity; capturing this plan
does not install helpers, provision hosts, or start the editor.

## 1. Adopt authoritative design revisions before runtime work

- [x] 1.1 Review `brainstorm.md`, `design.md`, and `specs/*/spec.md` under `openspec/changes/formalize-unity-feature-delivery/`; record adopted versus revised defaults in those planning artifacts, with no unresolved scope-changing decision before proceeding.
- [x] 1.2 Append superseding entries to `docs/decisions.md` for the design matrix, preserving D-01 through D-18 text; verify each changed rule names its predecessor, rationale, and rejected alternative.
- [x] 1.3 Reconcile `docs/boundary-contract.md` and `docs/adapters.md` for Codex delegated apply, explicit task/test links, format compatibility, ownership migration, protected manifests, and test-scope bounds; verify worked valid/invalid examples agree with the new decisions.
- [x] 1.4 Reconcile `docs/verification.md` and `docs/loop-control.md` for TDD evidence, shared failures, retry timing, sequential snapshots, recovery, review outcomes, and acceptance-gated flush; verify their state/action tables have no conflicting transitions.
- [x] 1.5 Update `HANDOFF.md`, `docs/README.md`, and `contracts/queue-reorder.example.json` to the adopted design and staged acceptance criteria; verify original Phase 0-7 order remains and the example represents shared tests and valid ownership scope.
- [x] 1.6 Reconcile `docs/adapters.md` and `docs/dev-environment.md` with the external module worktrees, complete nested-repository host, target coding profile, original design/wiki inputs, and existing HTTP Bridge; verify the documented graph matches `openspec/changes/formalize-unity-feature-delivery/design.md` and distinguishes installed code from unverified live execution.

## 2. Phase 0: reproducible package and stub graph

- [x] 2.1 Replace `requirements.txt` with `pyproject.toml`/`uv.lock`, pin `.python-version` to Python 3.12, and update `.env.example`; verify `uv sync` succeeds and every proposed dependency has an explained purpose.
- [x] 2.2 Replace the superseded package/graph and retire `tests/test_core.py` as specified in `HANDOFF.md`, creating `src/unity_coder/core/__init__.py`, `src/unity_coder/adapters/__init__.py`, and a stub `src/unity_coder/graph.py`; verify clean zero-test collection using the adopted Phase 0 empty-suite convention.
- [x] 2.3 Verify `langgraph.json` loads the rebuilt stub with `uv run langgraph dev --allow-blocking`; observe the graph listed without provider keys or Unity, stop the owned server, and record evidence in `HANDOFF.md`.

## 3. Phase 1: contracts, ownership, and explicit relationships

- [x] 3.1 Author `tests/test_contracts.py` and `tests/fixtures/contracts/` for collisions, empty owns, specs protection, adapter case behavior, invalid dependencies, shared tests/task mappings, consecutive versions, migrations, and budget lineage; run `uv run pytest -q tests/test_contracts.py` to record meaningful RED, then freeze these files.
- [x] 3.2 Implement typed loading/validation in `src/unity_coder/core/contracts.py` and `src/unity_coder/core/ownership.py`; verify all frozen contract scenarios pass without language-specific imports or hardcoded case folding.
- [x] 3.3 Refactor the contract implementation within ownership and rerun `uv run pytest -q`; verify no frozen fixture/test changed and update `docs/boundary-contract.md` with the validated wire examples.
- [x] 3.4 Run `uv run langgraph dev --allow-blocking`, confirm compilation/listing and stop the owned server; record Phase 1 criteria met/unmet in `HANDOFF.md` without requiring network or provider keys.
- [x] 3.5 Before extending the loader, author `tests/test_target_profiles.py` for separate host/game roots, module-relative owns, immutable allowed mounts, coding-rule hashes, and source provenance; observe meaningful RED and freeze it, then implement `src/unity_coder/core/target_profiles.py`, refactor, and verify `uv run pytest -q tests/test_target_profiles.py`; update `docs/boundary-contract.md` with portable examples and rejection of shared-module claims.

## 4. Phase 2: adapter protocol and structural conformance

- [x] 4.1 Author and freeze `tests/test_adapters.py` and `tests/fixtures/csharp/` after meaningful RED for parse/signature failures, generated-file exclusion, binding-interface preservation, and adapter-selected path rules; verify tests require no Unity installation.
- [x] 4.2 Implement `src/unity_coder/core/adapters.py`, typed results in `src/unity_coder/core/evidence.py`, and structural checks in `src/unity_coder/adapters/unity/`; verify frozen tests pass with tree-sitter and core contains no Unity/C#/dotnet behavior.
- [x] 4.3 Refactor adapter code, rerun `uv run pytest -q tests/test_adapters.py`, and update `docs/adapters.md`; verify structural violations identify the file/symbol and generated exemptions do not bypass protected-manifest checks.

## 5. Phase 3: independent tests and frozen TDD dispatch

- [x] 5.1 Author `tests/test_tdd.py` and `tests/test_dispatch.py` for test-first dispatch, global freeze barrier, meaningful Red, already-passing coverage review, defective tests, Green/Refactor, and missing-peer shared-test states; record meaningful RED then freeze them before implementation.
- [x] 5.2 Implement `src/unity_coder/core/tdd.py` and `src/unity_coder/core/dispatch.py` with fake agents; verify no impl unit dispatches before freeze and frozen tests/configuration cannot be modified.
- [x] 5.3 Implement bounded test preparation and Refactor/no-change transitions in `src/unity_coder/core/tdd.py`; verify expected Red is excluded from failed-implementation counts and all model calls remain accounted for.
- [x] 5.4 Refactor the dispatch/TDD implementation, rerun `uv run pytest -q tests/test_tdd.py tests/test_dispatch.py`, and update `docs/verification.md`; verify stage names remain separate from attempt trends.

## 6. Phase 4: blocking verification ladder and shared evidence

- [x] 6.1 Author and freeze `tests/test_verification.py` with fake transport scenarios for each failing rung, stop-first behavior, focused/full suites, zero/absent/skipped/inconclusive tests, stale results, and operational failure after meaningful RED.
- [x] 6.2 Implement `src/unity_coder/core/verification.py` and fake transport support in `tests/fakes.py`; verify each gate stops correctly and no model-facing result contains raw Unity logs.
- [x] 6.3 Author and freeze `tests/test_integration_failures.py` after meaningful RED for shared-test relationships, coordinated repairs, ambiguous routing, and dependent-evidence invalidation.
- [x] 6.4 Implement shared evidence/routing in `src/unity_coder/core/integration.py` and `src/unity_coder/core/evidence.py`; verify multi-unit failures retain per-unit classification without bisection or blame-by-file/test-name.
- [x] 6.5 Refactor integration/verification code, run `uv run pytest -q`, and update `docs/verification.md`; start/list/stop the graph with `uv run langgraph dev --allow-blocking` and record all Phase 4 acceptance results in `HANDOFF.md`.

## 7. Phase 5: retry trends, escalation, and dossiers

- [x] 7.1 Author and freeze `tests/test_loop_control.py` and `tests/test_dossiers.py` after meaningful RED covering comparable evidence, immediate STALLED, first/second regression, successful last attempt, unconditional failed exhaustion, and mixed per-unit defect classes.
- [x] 7.2 Implement `src/unity_coder/core/loop_control.py` and `src/unity_coder/core/dossiers.py`; verify frozen scenarios pass and implementation repair never crosses the Architect boundary unless deterministic escalation requires it.
- [x] 7.3 Refactor loop/dossier code and run `uv run pytest -q`; update `docs/loop-control.md` and `HANDOFF.md` with Phase 5 criteria and evidence that regression restores only affected owned state and invalidates dependent results.

## 8. Offline workspace isolation, status, and recovery prerequisites

- [x] 8.1 Author and freeze `tests/test_workspaces.py` using temporary nested Git repositories after meaningful RED for per-unit bases, owned-file capture, stale dependencies, protected metadata, coordinator-only integration, module-only external worktrees, and rejection of worktrees under Unity import.
- [x] 8.2 Implement coordinator workspace management in `src/unity_coder/core/workspaces.py` and execution-host policy checks in `src/unity_coder/core/execution_host.py`; verify worktrees do not grant agents access to shared trees/metadata and unsupported isolation fails preflight.
- [x] 8.3 Author and freeze `tests/test_recovery.py` and `tests/test_progress.py` after meaningful RED for crash-after-apply, active-verifier restart, stale result rejection, atomic status, sequence/heartbeat, cancellation, and operational cleanup.
- [x] 8.4 Implement `src/unity_coder/core/journal.py`, `src/unity_coder/core/progress.py`, and `src/unity_coder/core/lifecycle.py`; verify injected failures never duplicate a patch or accept evidence for another candidate.
- [x] 8.5 Refactor workspace/lifecycle code, run `uv run pytest -q tests/test_workspaces.py tests/test_recovery.py tests/test_progress.py`, and update `docs/verification.md`/`docs/loop-control.md`; verify user starting work is unchanged after failure or cancellation.
- [x] 8.6 Author and freeze `tests/test_candidate_materialization.py` after meaningful RED for one game mount, metadata-preserving synchronization, stale managed deletions, junction escape, fixed nested dependencies, import-generated metadata reconciliation, and host drift; implement/refactor `src/unity_coder/adapters/unity/materialization.py` and verify `uv run pytest -q tests/test_candidate_materialization.py` with fake hosts, then document safe provisioning and output locations in `docs/adapters.md`.

## 9. Offline presentation integrity and human-review prerequisites

- [x] 9.1 Author and freeze `tests/test_presentation.py` using fake manifests after meaningful RED for frozen content, GUID/import integrity, serialized interfaces, declared runtime mutations, reuse of existing scenes/assets, identical baseline distribution to external worktrees and verification, target placeholder naming, and artist replacement requirements.
- [x] 9.2 Implement generic manifests in `src/unity_coder/core/presentation.py` and Unity-specific structural reporting in `src/unity_coder/adapters/unity/`; verify changing a protected .meta identity fails despite generated-file ownership exemption.
- [x] 9.3 Author and freeze `tests/test_human_review.py` after meaningful RED for awaiting review, revision-bound approval, implementation repair versus contract rework, nonrunnable failures, and metadata-only completion provenance.
- [x] 9.4 Implement review records/resume in `src/unity_coder/core/review.py` and `src/unity_coder/core/lifecycle.py`; verify no agent can self-approve and any relevant candidate change requires fresh verification/review.
- [x] 9.5 Refactor presentation/review code, run `uv run pytest -q tests/test_presentation.py tests/test_human_review.py`, and update `docs/boundary-contract.md`/`docs/loop-control.md` with the validated baseline and review formats.

## 10. Phase 6: real Unity preparation and sequential EditMode integration

- [x] 10.1 Author and freeze offline adapter/transport boundary tests in `tests/test_unity_transport.py` after meaningful RED for request provenance, bounded Bridge discovery, wrong-project refusal, reload/task-ID loss, nested command errors, command success before test completion, missing tooling, timeout recovery, and normalized output; verify tests require neither network nor Unity.
- [x] 10.2 Implement the Bridge worker transport in `src/unity_coder/adapters/unity/transport.py` and a request-specific game-local command template replacing the unverified `unity/Editor/UnityCoderVerifier.cs`; reuse `IUnityOpCommand`/`TestRunnerApi`, persist callback-driven results, and verify frozen transport tests pass without modifying shared packages or requiring MCP installation.
- [x] 10.3 Reuse existing game PSD/prefab/map/binding tooling through Architect-side preparation support under `unity/Editor/` and document the manifest contract in `docs/adapters.md`; verify on the dedicated configured host that required feature shells compile, existing bindings resolve, `_placeHolder` assets import under `GAME_ROOT/Runtime/Resource/monopoly/`, and original designs in `GAME_ROOT/Docs~/` are unchanged.
- [x] 10.4 Validate new-file compile inclusion on the scratch project and record commands/timing in `docs/dev-environment.md`; verify an intentionally invalid newly added source file fails the compile gate, or record and implement the adopted fallback before trusting it.
- [x] 10.5 Demonstrate at least two coding units with isolated worktrees and one sequential EditMode worker; record Red, Green, Refactor, shared-test routing, full-suite evidence, and frozen-baseline integrity in `openspec/changes/formalize-unity-feature-delivery/verification.md`.
- [x] 10.6 Integrate the real coder and independent judge behind tested seams in `src/unity_coder/core/` without stack-specific behavior; verify distinct model IDs, temperature zero by default or explicitly approved provider control under D-28, authorship/notes exclusion, and one real unit completing on the scratch project.
- [x] 10.7 Refactor Unity/model boundaries, rerun `uv run pytest -q`, and update `HANDOFF.md` with Phase 6 criteria met/unmet; verify scratch-project prerequisites do not leak into the offline suite.
- [x] 10.8 Before live task 10.3 and other real-Unity checks, document the target profile from `GAME_ROOT/AGENTS.md`, `.codex/rules/`, `.codex/reference/`, `Docs~/`, and existing `openspec/` in `docs/adapters.md`; verify source/rule hashes, actual assembly/resource identities, Tuanjie/package versions, and preserved authoritative design provenance without duplicating the game's planning system.
- [x] 10.9 After task 10.8 and before live task 10.3, provision the complete disposable `UNITY_HOST/` only at an authorized location with recorded nested-module/package/settings identities, install the packaged test helper only under `GAME_ROOT/Editor/Script/` or its existing Editor-only `Tests/Runtime/Script/`, and verify exactly one game mount plus no shared source changes; record prerequisites or blockers in `openspec/changes/formalize-unity-feature-delivery/verification.md`.
- [x] 10.10 After task 10.9, verify the live Bridge for the exact `UNITY_HOST/` project, discover required commands/tests, and record a request-specific EditMode result and reload/reconnect evidence in `openspec/changes/formalize-unity-feature-delivery/verification.md`; if unreachable, record operational failure without starting another editor, installing packages, or claiming compilation/test success. Live tasks 10.3-10.6 depend on this readiness check.

## 11. Phase 7: durable governors, cycle branches, and accepted provenance

- [x] 11.1 Author and freeze `tests/test_budget.py`, `tests/test_branches.py`, and `tests/test_constraints.py` after meaningful RED for pre-dispatch reservations, uncertain usage, resume/migration continuity, cycle growth limits, abandon restoration, and accepted-only constraint flush.
- [x] 11.2 Implement `src/unity_coder/core/budget.py`, `src/unity_coder/core/branches.py`, and `src/unity_coder/core/constraints.py`; verify exhaustion stops new calls, retains cycle candidates, preserves user work, and does not reset budgets on review or migration.
- [x] 11.3 Verify managed constraints retain provenance, deduplicate, cap at 40 with archive, and preserve unrelated `AGENTS.md` content using `uv run pytest -q tests/test_constraints.py`; verify the final metadata revision derives only from the approved candidate.
- [x] 11.4 Refactor governor/branch/constraint code, run `uv run pytest -q`, and update `docs/loop-control.md`/`HANDOFF.md`; verify Phase 7 acceptance distinguishes automated readiness from accepted pass and performs no mainline write/push.

## 12. Delegated apply integration and final acceptance

- [x] 12.1 Author and freeze `tests/test_architect_boundary.py` after meaningful RED for existing game OpenSpec/context discovery, design/wiki/rule provenance export, task links, format mismatch, progress reconnect, structured outcomes, partial tasks, review resume, and contract rework using fake executor/model boundaries.
- [x] 12.2 Implement local invocation/result handling in `src/unity_coder/cli.py` and a maintained delegated apply skill at `.agents/skills/framework-apply/SKILL.md`; verify the skill uses schema-discovered context and does not edit upstream generated apply skills or require a custom schema.
- [x] 12.3 Refactor the boundary implementation and rerun `uv run pytest -q tests/test_architect_boundary.py`; document a worked OpenSpec-to-contract-to-review cycle in `docs/boundary-contract.md` and verify only the Architect updates planning task status.
- [x] 12.4 Rehearse human acceptance on the exact scratch-game candidate, including a broken-interaction repair and a presentation-change rework; record explicit review identity/revision/evidence in `openspec/changes/formalize-unity-feature-delivery/verification.md` and verify stale approval is rejected.
- [x] 12.5 Rehearse compatible and incompatible placeholder replacements as separate scratch-project changes; record preserved references, manifest checks, and renewed visual review in `openspec/changes/formalize-unity-feature-delivery/verification.md` without replacing assets inside the coding cycle.
- [x] 12.6 Perform spec compliance review against all four `specs/*/spec.md` deltas in this change, then code-quality review of rebuilt `src/unity_coder/`, `tests/`, and `unity/Editor/`; record actionable findings and resolve them without changing frozen tests to match code.
- [x] 12.7 Run fresh `uv run pytest -q` and `uv run langgraph dev --allow-blocking`, confirm graph compilation/listing and stop the owned server; write final `openspec/changes/formalize-unity-feature-delivery/verification.md` with commands, outcomes, reviewed revisions, and each phase criterion met/unmet, explicitly naming any unverified real-Unity acceptance.

## Workflow follow-up

- Review the completed implementation and evidence before synchronizing capability deltas into `openspec/specs/`.
- Archive through OpenSpec only after its completion, review, and synchronization checks are satisfied; preserve any user-required approval gates.
- Final-art production, automated PlayMode policy, additional adapters, and remote workers require separate future changes.
- Keep live target connectivity, host provisioning identities, private package access, new-file compile inclusion, and test duration visible as deployment acceptance work; static inspection is not passing runtime evidence.
