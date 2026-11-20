# Tasks

Paths are relative to the independent game module unless marked as framework planning or trusted state. Preserve the approved proposal and existing run/budget identities. CLI-exported task IDs determine runtime task links after this revision. Checkboxes remain subject to Architect reconciliation under the framework's human-review rules.

## 1. Bind and prepare the baseline

- [ ] 1.1 Reconnect `trusted-state/host-overlay/overlay.json`, `trusted-state/budget-policy.json` and prior receipts. Verify the Bridge's project identity, idle compile/test capabilities and the recorded original baseline. Retain run ID `monopoly-game-lobby` and the existing ceilings. Record current readiness in the planning change's `verification.md`.
- [ ] 1.2 Trace the existing entry through `Runtime/Script/Monopoly.cs` and `Runtime/Script/MonopolyRootScene.cs`. Pin the exact existing-file exception inventory for the approved game/scene entry. Verify original bytes against the preserved host baseline and list paired entry/exit/cleanup behaviors in the runtime entry inventory.
- [ ] 1.3 Extend the rehearsal-only trusted overlay with the exact entry-exception register and preparation-asset receipts. Preserve the original baseline and sidecars. Run `check_overlay.py` with regressions for declared replacement, undeclared overlap, baseline drift, interrupted writes, imported metadata and stale candidates. Rehearsal host wiring stays outside framework runtime.
- [ ] 1.4 Prepare compilable `Runtime/Script/UI/LobbyRehearsal/LobbyPorts.cs`, `LobbyDtos.cs`, `LobbyConfiguration.cs` and the five units' owned shell files from design.md. Inspect the existing target APIs before binding Navigator, resources, account storage, schedule, sound, quality and cameras. Verify all shells compile on the dedicated host before creating behavioral expectations.
- [ ] 1.5 Create `Runtime/Resource/monopoly/Scenes/LobbyRehearsal/LobbyStreet_placeHolder.unity`, the ten declared view prefabs under `Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/` and original geometric/animation/configuration assets within those overlay roots. Verify Western street geometry, 3D character/vehicle, Idle/Wave/Celebrate, hierarchy, references, safe areas and duplicate camera/event facilities through live import and inspection.
- [ ] 1.6 Capture prepared assets and Unity metadata into a new coordinator baseline. Write `specs/monopoly-game-lobby/presentation.json` with hashes, asset identities, serialized bindings, protected layout, launch entry and artist-replacement requirements. Reopen/inspect the actual scene and prefabs, confirm their committed bytes match the host, and record preparation evidence.

## 2. Export a validated execution handoff

- [ ] 2.1 Refresh `pnpm exec openspec instructions apply --change rehearse-monopoly-game-lobby --json` in the framework store. Export its portable context and original source/rule identities to `specs/monopoly-game-lobby/planning-context.json`. Verify hashes and all returned task references. Retain raw machine-specific CLI output in transient local storage.
- [ ] 2.2 Prepare `specs/monopoly-game-lobby/spec.md`, `coding-profile.json`, `environment.json` and the exact entry inventory. Export the 119-story/143-functional-item mapping and approved rehearsal overrides. Verify the bounded module mount, current dependency revisions, assembly identity, original entry hashes and protected files.
- [ ] 2.3 Validate `specs/monopoly-game-lobby/contract.v1.json` with the current Unity adapter and contract/profile loaders. Bind actual shell ownership, test authors, exact anticipated test IDs, shared criteria, dependencies, task links and presentation/profile hashes. Confirm no implementation ownership intersects frozen tests or presentation inputs.
- [ ] 2.4 Compose a rehearsal-only trusted production host using ArchitectBoundary, ProductionExecutor, held RunLease, existing BudgetLedger, WorkspaceManager, ModelCodingWorkers, blocking Unity verification, overlay preflight and authenticated ReviewGate. Preflight role/model identities and prompt reservations against the unchanged budget. Verify that implementation worktrees cannot access trusted state or human-review callbacks.

## 3. Author, review and freeze acceptance tests

- [ ] 3.1 Author `Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationTests.cs` for mapped L1/L2/NFR stories, imported geometry/bindings, existing entry, platform home, wallet formatting, route/back behavior, safe areas and account isolation. Verify compilation and explicit test discovery.
- [ ] 3.2 Author `Tests/Runtime/Script/LobbyRehearsal/LobbyEconomyTests.cs` for mapped L3/L7/L12 stories and approved catalog, purchase, expiry, checkout, cards, VIP, restart and clock rules. Include failed/retried transactions, exactly-once card grants and Unicode-independent numeric boundaries. Verify compilation and discovery.
- [ ] 3.3 Author `Tests/Runtime/Script/LobbyRehearsal/LobbyMatchTests.cs` for mapped L9/L10/L11 stories, multiplier 10, party synchronization, invitation races, cancellation, atomic fees, bot fill, preserved disconnected seats, abandonment and deterministic settlement. Verify compilation and discovery.
- [ ] 3.4 Author `Tests/Runtime/Script/LobbyRehearsal/LobbySocialTests.cs` for mapped L4/L13 stories, friend caps/expiry/recommendations, message permissions, Unicode length, cooldown, reporting, draft retention and separate unread counters. Verify compilation and discovery.
- [ ] 3.5 Author `Tests/Runtime/Script/LobbyRehearsal/LobbyRecordsSettingsTests.cs` and `LobbyJourneyTests.cs` for mapped L5/L6/L8 stories and shared entry/recharge/party/result/account journeys. Verify shared snapshot windows, row limits, accounting, quality/audio behavior and simulated support.
- [ ] 3.6 Obtain configured independent-judge review of validity and complete source/decision coverage. Run the declared EditMode baseline sequentially and record intended behavioral Red, discovered/executed IDs, all counts and baseline hashes. Treat setup, compile and unexpected skip results as preparation failures. Freeze all tests, assembly/selection configuration and metadata before any implementation unit is dispatched.

## 4. Delegate implementation against frozen inputs

- [ ] 4.1 Dispatch SHELL for `Runtime/Script/Monopoly.cs`, `Runtime/Script/UI/LobbyRehearsal/Monopoly.LobbyRehearsal.cs`, `LobbyShellBindings.cs` in that UI root, and `Runtime/Script/UI/LobbyRehearsal/LobbyRehearsalPanel.cs`. Verify mapped presentation/entry tests, real lifecycle routing, fake platform return and review-panel controls. Retain Green evidence and verify Refactor within frozen ownership.
- [ ] 4.2 Dispatch ECON for `Runtime/Script/UI/LobbyRehearsal/LobbyEconomy.cs`. Verify mapped wallet, catalog/appearance, clock/persistence, checkout, card/VIP and restart tests. Retain Green evidence and verify Refactor.
- [ ] 4.3 Dispatch MATCH for `Runtime/Script/UI/LobbyRehearsal/LobbyMatch.cs`. Verify mapped invitation/party, queue, fee, handoff and result tests, including shared tests against declared peers. Retain Green evidence and verify Refactor.
- [ ] 4.4 Dispatch SOCIAL for `Runtime/Script/UI/LobbyRehearsal/LobbySocial.cs`. Verify mapped friend, chat, moderation and unread tests. Coordinate recommendation/result inputs through frozen interfaces. Retain Green evidence and verify Refactor.
- [ ] 4.5 Dispatch RECORDS for `Runtime/Script/UI/LobbyRehearsal/LobbyRecordsSettings.cs`. Verify mapped ranking/history/recommendation and settings/support tests with shared income data. Retain Green evidence and verify Refactor.
- [ ] 4.6 Invoke and reconnect through `unity_coder.cli.invoke_local(boundary, executor)`, reusing durable completed receipts. Verify original/frozen/candidate hashes around every materialization and sequential ladder, reconcile generated metadata into committed candidates and retain paid-call usage. Record operational stops or framework defects with exact evidence.

## 5. Review the integrated candidate

- [ ] 5.1 Run the full required integrated lobby EditMode selection sequentially against the exact materialized revision. Confirm complete requested/discovered/executed correspondence, expected assertion outcomes and zero unexpected skips/inconclusive results. Record exact contract, presentation, profile and candidate identities in the planning change's `verification.md`.
- [ ] 5.2 Perform specification compliance review using the complete story/scenario/test map. Verify all approved overrides and source exclusions. Record criteria met/unmet and findings in `verification.md`, route implementation findings to bounded repair, and route contract/layout findings through the documented revision transition with the same run budget.
- [ ] 5.3 Perform code quality review after compliance review. Verify target lifecycle/API conventions, ownership, transaction/retry consistency, frozen inputs and preservation of unrelated host files. Resolve findings through delegated changes and rerun affected and final acceptance selections.
- [ ] 5.4 Prepare a candidate-bound review package with the existing launch entry, exact 3D scene/prefab identities, Editor peer/time/account instructions, normal journeys, visual checks at the three portrait ratios, selected test receipts and explicit evidence limits. Verify durable outcome `awaiting_human_review` and pending human decision. Record the skill sufficiency, supplied wiring, budget usage and remaining limits in the existing rehearsal report.

## Workflow follow-up

- The user reviews the exact candidate and supplies a decision. Authenticated acceptance, later task reconciliation and any production delivery use the documented Architect boundary.
- Spec synchronization, archive, mainline integration and publication are separate follow-up actions when requested.

