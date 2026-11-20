# Safe same-run recovery — 2026-11-19

Latest continuation: the user authorized twelve cycles and 6,000,000 input /
1,800,000 output tokens. Authenticated cycle and typed token recovery preserved
the same run and all accounting. The latest full framework suite passes 538
tests. Cycle 12 ended in native abandon at the cycle ceiling after independent
NFR test-preparation rejection; it did not reach human review. See
[token-amendment-report.md](token-amendment-report.md) and
[cycle12-report.md](cycle12-report.md). The six-cycle account below is retained
as history; its cycle-only grant remains supported unchanged.

The user authorized audited recovery after budget abandonment and continuation toward awaiting_human_review. The approved amendment raises the total contract-cycle ceiling from 3 to 6 while retaining 3,000,000 input tokens, 900,000 output tokens, two added units per rework, the same run ID, configured models and trusted overlay.

## Runtime implementation and verification

`core/recovery.py` supplies RecoveryGrant and recover_abandoned_run. The trusted host authenticates explicit session authorization bound to the run, previous contract and exact abandoned-result digest. Recovery requires a held lease, reconciled workers, a verified retained candidate and a consecutive validated contract. It archives the original result, invocation, budget, executor, dossier and progress bytes, preserving calls, unknown reservations, cycle history and unit lineage. It records intent first and publishes the amended ledger last. Interrupted operations reconcile original or intended bytes without replay. Conflicting evidence stops recovery. The implementation supports cycle exhaustion with remaining token allowance; it does not extend token budgets or bypass acceptance.

The 23 acceptance cases failed before implementation because the recovery module was absent, then passed. Frozen test SHA-256: `50dbd5a320a5f9b92739be193e2f46b5f29b4b778219bb88bdc2aaf601aa9fa1`. Existing cycle-transition tests and separate budget/governor/host-policy checks passed. Full offline suite: **526 passed**, one existing TestResult collection warning, 243.72 seconds. Graph compiled/listed as unity_coder under process-local PYTHONUTF8=1; owned server stopped. OpenSpec validation passes. No dependencies were added.

D-29 records the narrow superseding recovery decision. Existing settled decisions remain unchanged. Proposal/design/brainstorm were reconciled with the authorized amendment; product choices, scene/prefab identity and acceptance scope remain unchanged. Preparation created contract v4 in a new external worktree, descended from retained candidate `c5143932bf382787c5504793a44871b8a2a48c3a`, without handwritten lobby implementation. New author-owned recovery notes force native delegated test repair and independent review before Red and global freeze.

## Live continuation

Recovery succeeded with 918,325 input / 300,946 output tokens retained, all 30 earlier calls intact, and the original 81,134-file baseline verified. Contract version 4 then used the raised per-stage allocations and performed real delegated authorship and independent review. It ended in native rework at candidate `6523bafd05295d0dc3487e062b074699d63d3f32` after three rejected presentation-test attempts, with cumulative usage 1,356,499 input / 395,088 output. No tests were frozen or implementation dispatched.

The resulting dossier exposed concrete preparation defects: missing shared-wallet prefab provenance, outside-menu input and separate marquee unread badge, plus incomplete authoritative source context. Version 5 addresses those with a shared wallet nested by Lobby and Recharge, explicit Outside/MarqueeBadge bindings, package/Root/VM source context, exact observation guidance, and the same coder's supported low reasoning for test authors when no effort is configured. Explicit configured effort, provider routing, models and temperature remain unchanged. The new offline reasoning policy test was Red then frozen at SHA-256 `58a71651ddd230a645b190c1f201fe044e1b5d5ac68e25b0aa462a211153870d`; all eight policy/wiring tests and the earlier transport check pass.

Actual host compilation rejected the delegated harness's `EditorSceneManager.OpenPreviewScene` with CS0117. Its never-frozen body and the rejected presentation suite remain in Git history and were copied into v5 provenance before compile-only containers were restored. The corrected preparation-only candidate `7ceb5df2b1c1ccd993c9b360b6e7619cbe1e2618` compiled on the actual host. Functional fixture implementation remains delegated, using owned additive Editor scenes with explicit cleanup.

The Editor-only asset repair captured exactly two revised prefabs plus one new shared-wallet prefab and its metadata. It preserved before/after bytes, audited every original file, restored prior managed bytes before the unchanged overlay's additive capture, then materialized committed candidate `91ee94eed8f85e6f9a4a19ba267a34b8e6dcd8d6`. No overlay code or original-file checks were weakened. Tuanjie's metadata GUID is opaque; both serialized nested source references were checked for the same actual Editor GUID while imported metadata bytes were preserved verbatim.

The native same-run rework transition activated version 5 at baseline `93c48f3a7ce80a5d12e9d56f71c033e9573dac16`, contract SHA-256 `8723e6c2300685d4fee28fe6f896706a4234b0f7af4fa8dc83b45b1a1e7e6a07`. Version 5 ended in native rework at candidate `b66accbbd5bf5c53e573cb4138463d3d5d3231d4`, with cumulative usage 2,059,292 input / 592,190 output. The combined presentation author still produced contradictory lifecycle expectations and ineffective architecture/preference oracles.

Version 6 split the eight core presentation methods and four NFR methods into two specialist authors. Explicit ownership migrations retained both specialists' accounting/repair lineage from TEST-SHELL, which became superseded. All 125 test selections and all 119 source-story mappings remain, with explicit new class aliases in story-test-map.v6.json and acceptance-conditions.v6.json. No product clauses were waived. The consecutive native transition activated baseline `8539d3c0791be2eb9836a6c262292e29e50e6788`, contract SHA-256 `eb8ea839e6df24832cb0cd75ce6532feaa0fb1dfbecaff66c054b1b7d58c88ac`.

Read-only prompt curation now omits unrelated test methods/comments for implementation while retaining every mapped method and all helpers, with original source hashes. Refactor prompts retain code, specification and test provenance; execution still uses the full frozen selection. These changes have three additional frozen offline cases, making eleven separate host-policy/context cases pass. No framework runtime beyond the authorized token/recovery plumbing was changed.

## Final result: authorized budget stop, not human review

The same run ended **abandon / budget at contract version 6** after the core specialist's third preparation rejection. The exact retained test-preparation candidate is `d6a1ab346e65e5b320621b784607b647834809dc` on `agent/monopoly-game-lobby/cycle-6`. The native governor detached the managed integration worktree back to baseline `8539d3c0791be2eb9836a6c262292e29e50e6788`, preserving the retained branch. It did not reach awaiting_human_review.

| Resource | Ceiling | Used | Remaining |
|---|---:|---:|---:|
| Input tokens | 3,000,000 | 2,507,338 | 492,662 |
| Output tokens | 900,000 | 673,592 | 226,408 |
| Contract cycles | 6 | 6 | 0 |

The final independent findings are in evidence/dossier-v6.json:

1. Existing-entry tests suppress exceptions and permit no-op entry/resume/launch/cleanup paths rather than proving each with live ownership.
2. The shared-formatter oracle inspects a literal character, not actual formatter calls; it can accept duplicate implementations and reject valid ones.
3. Rendering/animation assertions are not bound to the equipped character and relevant camera, and Back's return to Lobby is not established.
4. Upper-right menu/marquee placement and pointer-layout ordering remain incompletely observed.

These are semantic test-validity/coverage failures in complete coder responses, not the old output-token ceiling. The independent judge was not weakened or bypassed. Global test freeze: **false**. Selected lobby Unity tests executed: **0**. Delegated functional implementation dispatch: **0**. No functional lobby candidate, pending human-review offer, human approval, mainline commit, push or merge exists. Runtime recovery itself is implemented and verified, but the requested feature remains incomplete.

The final full original host byte check passed for all 81,134 files; evidence/recovery-final-v6.json records the unchanged baseline/overlay identities, zero pending metadata, 57 settled calls (31 coder / 26 judge) and no human acceptance. The host retains the imported preparation candidate, not a functional lobby build. The already authorized six-cycle allowance is exhausted; further paid continuation requires an explicit bounded cycle amendment. No additional amendment or token reset was performed.

## Review instructions

Review src/unity_coder/core/recovery.py, the appended D-29, and the 23 frozen recovery tests as the runtime repair. Reproduce the focused offline checks with `uv run pytest -q tests/test_abandoned_recovery.py tests/test_cycle_transition.py`. Inspect the retained candidate with `git -C <external-rehearsal-root>/module show d6a1ab346e65e5b320621b784607b647834809dc` and read evidence/dossier-v6.json. Treat that candidate as rejected test preparation only. The dedicated host's existing Monopoly Game/Scene entry is not yet a functional lobby review entry. Do not record a game acceptance decision against this candidate.

## Skill observations

framework-architect/framework-apply specify the required host, accounting continuity, candidate identity, frozen tests, sequential verification and human review boundary. They previously described only operational resume and completed-rework transitions. The explicit new runtime API supplies the missing abandoned-run recovery capability; the trusted host supplies session authorization provenance and concrete Git/worker/baseline reconciliation. No approval is inferred from automated success.

Runtime recovery source SHA-256: `e79c652f6290a2582d4bf8f5ea25d7c7ba1d9699170d081830f41a1ced3aa86a`. The new runtime file is uncommitted and reviewable separately from the incomplete game feature.

The skill instructions were sufficient to keep source review separate from execution, require real Red/freeze before implementation, preserve host identities and stop at the declared budget. The missing wiring included target-verified scene APIs, complete Root/VM context, serialized shared-wallet/input/badge references and stage-aware prompt curation. Source-heavy author granularity remained inadequate for the configured coder within the six-cycle allowance: complete responses continued to contain ineffective test oracles. The report does not treat source approval as compiled execution or model feedback as human acceptance.
