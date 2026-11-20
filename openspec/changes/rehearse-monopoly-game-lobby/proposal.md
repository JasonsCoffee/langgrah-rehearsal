# Proposal

## Why

Deliver a fully functional client-side Monopoly lobby rehearsal covering the supplied main-interface design, requirement analysis and user stories. Deterministic fake services make the complete lobby journey reviewable while the production platform and server integrations are pending.

## What Changes

### Presentation and entry

- Build a fully 3D Western-style street with original placeholder geometry, a 3D character and vehicle, and actual scenes and prefabs. Character preview actions are Idle, Wave and Celebrate.
- Use or replace the existing Monopoly Game/Scene entry to open the lobby with fake platform entry and exit. The lobby return button immediately opens a simulated platform home screen. Its “重新进入大赢家” action uses that same entry.
- Preserve the portrait 1080 × 2160 layout, safe-area adaptation and framework VVMP/Navigator integration. The central 3D region between the top controls and marquee opens appearance settings. Visible buttons receive their own clicks.
- The bottom smiley opens Chat. The second circular button opens Invite teammate at the Friends page's cooperation-partner tab.
- Implement the L1–L13 client flows, including wallet, appearance, friends, rankings, history, shop, settings, tier selection, matching, parties, recharge/VIP and chat. Retain the documented in-game invitation scope and local unread indicators.

### Wallet, catalog and appearance

- Use configurable new-account balances of 10,000 coins and 200 ingots. Display, copying, friend lookup and invitations share one synthetic platform account ID.
- Keep a game-owned catalog for models, prices and display rules. A fake game appearance service manages player unlocks, expiry times and equipped selections.
- Supply six skins and four vehicles covering permanent defaults, purchasable permanent items and timed items, plus the “无座驾” option. Seven-day ownership begins at successful purchase using the fake server's clock. Expired equipped items immediately fall back to eligible defaults with a brief notification.
- Configurable skin prices are 1,000 coins permanent and 300 seven-day. Vehicle prices are 3,000 coins permanent and 900 seven-day.
- Sort shop items by `shopPriority` descending, then `id` ascending, with owned items last. Reorder when the shop is reopened. Preserve confirmation, preview, equip and insufficient-balance recovery flows.
- Persist balances, purchased appearances, equipped selections and card entitlements across Play Mode restarts, isolated by synthetic account ID.

### Matching, parties and results

- Configure the five base values 10 / 50 / 250 / 1000 / 5000 with an entry-fee multiplier of 10, producing fees of 100 / 500 / 2,500 / 10,000 / 50,000 coins. The multiplier remains configurable.
- Parties contain up to two players who enter the same match and faction. Either member changing the tier updates both players' selection and displayed fee. Either member can start matching after the fake service validates both balances, or cancel for both while preserving the party and tier. Charge fees when the match starts.
- Use the documented configurable three-second matching heartbeat and 24 seats. After a configurable 30-second maximum wait, fill remaining seats with fake bots and start automatically. Each bot receives a synthetic in-match balance equal to the tier's entry fee.
- Invitations expire after a configurable 30 seconds. A player's first successful acceptance determines their party and closes their other invitations. The second member joining closes the inviter's remaining invitations. Acceptances already in flight receive “队伍已满”.
- A disconnect at match entry preserves the seat and party assignment, simulates temporary AI control and allows reconnection through the fake match service.
- Successful matching opens a rehearsal handoff view showing the tier, charged fee, 24 seats and faction assignments. Returning requires abandonment confirmation, records “已放弃”, retains the fee and prevents rejoining that match.
- Provide “完成模拟对局” to apply a deterministic fake result, settle the wallet once, update history and rankings, and return to the lobby.
- For abandoned matches, total expenses equal total income plus entry fee, profit equals negative entry fee, and the rank column shows “已放弃”. Completed matches display the final rank supplied by the fake match service.

### Friends, records and chat

- The fake platform supplies a configurable 100-friend limit and removes unanswered requests after seven days using its clock. Historical-partner and qualifying-opponent recommendations each have a configurable limit of 20, using the documented eligibility rules.
- Rank positive income over rolling 24-hour and seven-day windows using the fake server's clock and a shared snapshot timestamp. Show ten ranked rows plus a pinned self row, retaining the documented 100-rank loading limit.
- Expand chat below the wallet bar with variable-height rows, scrollable history and input above the keyboard. Show the player's avatar beside their right-aligned messages.
- Use a configurable 200-Unicode-character limit for world and private messages. Reject overlong messages and preserve the draft. The fake chat service enforces a configurable three-second per-player world-chat cooldown with “发言过于频繁” feedback.
- Reporting uses long-press → 举报 → confirmation. The fake moderation service records the report and shows “举报已提交”.
- One shared service exposes separate private-message, world-message and pending-friend-request counters. The private total aggregates conversation unread counts. Opening World chat marks its messages read, including arrivals while visible. The marquee retains the latest successfully delivered world message, including the player's own messages. Private messages stay within private chat.

### Recharge, cards, VIP and settings

Use the following configurable simulated purchase and exchange tiers. Each row specifies an ingot purchase and a separate coin-exchange option.

| Purchase price | Ingots | Coins for exchanging that ingot amount |
| --- | --- | --- |
| ¥3 | 30 | 3,000 |
| ¥20 | 200 | 20,000 |
| ¥50 | 500 | 50,000 |
| ¥100 | 1,000 | 100,000 |
| ¥200 | 2,000 | 200,000 |
| ¥500 | 5,000 | 500,000 |

The approved card base schedule is the complete rehearsal entitlement.

| Card | Simulated price | Configurable duration | Purchase grant | Scheduled grant |
| --- | --- | --- | --- | --- |
| Monthly | ¥30 | 30 days | 15,000 coins | 1,500 daily |
| Golden annual | ¥298 | 365 days | 180,000 coins | 1,500 daily |
| Diamond annual | ¥998 | 365 days | 500,000 coins | 20,000 weekly |

- Repeat purchases extend validity from the later of current expiry or fake server time. Daily grants first fall due 24 hours after purchase, weekly grants after seven days, then repeat through expiry. Extensions continue the existing schedule. The fake service credits each due grant once, including catch-up for periods when the lobby was closed.
- The fake platform applies the original six-month VIP qualification rules, including immediate upgrades and first-of-month re-evaluation. The client displays supplied VIP data. Keep the documented benefit categories with original, Monopoly-specific rehearsal descriptions suited to entry fees. VIP is informational in this rehearsal, and the approved entry fees apply to every player.
- Store timestamps in UTC and use Asia/Shanghai for calendar-based rules. Rolling ranking windows remain elapsed-time windows.
- Map Low and High to the framework's lowest and highest supported quality tiers. Device rating selects the initial setting, and per-account saved choices override it. Preserve separate music/effect settings and the documented rules/about flows.
- Customer support opens a simulated platform support page with rehearsal help text and a return action to Settings.
- Add an Editor rehearsal panel for switching synthetic accounts, advancing the fake server clock and controlling synthetic peers. Peer controls trigger incoming messages, invitations, acceptance and disconnection while the active account stays logged in.

### Execution and acceptance

Continue the existing LangGraph rehearsal using the trusted overlay, independent external module repository, worktrees and trusted state. Retain the amended run-wide ceilings of 3,000,000 input tokens and 900,000 output tokens. The user subsequently authorized authenticated recovery after cycle-three abandonment with a total ceiling of six contract cycles; keep the limit of two added units per rework and preserve all usage and earlier cycles. Use the locally configured coder and independent judge with persistent accounting.

Prepare and verify the imported scene/prefab baseline before freezing the runtime contract. Map requirements and stories to exact units and tests, independently review tests, observe behavioral Red, and freeze tests before implementation dispatch. Delegate implementation through the framework and run focused and final declared Unity EditMode selections sequentially. Offer the exact verified candidate, behavior, test results and launch instructions at `awaiting_human_review`. Human acceptance belongs to the user.

## Capabilities

### New Capabilities

- `monopoly-game-lobby` covers the 3D portrait lobby, client navigation and settings, appearance and economy, social interactions, income records and the fake entry-to-match journey described above.

### Modified Capabilities

None.

## Impact

Target changes stay within `Assets/JJGame/monopoly/` and its necessary Unity-generated metadata. New feature files use the existing LobbyRehearsal overlay subtrees. The user-authorized existing game/scene entry changes require exact file ownership and original-byte hashes in the downstream design and contract. Extend the trusted overlay's preservation checks for those bounded entry changes while retaining baseline and import-drift checks for unrelated files.

This is an actual-feature rehearsal following the completed framework implementation handoff. Governing design remains in `docs/boundary-contract.md`, `docs/verification.md`, `docs/loop-control.md`, `docs/adapters.md` and `docs/decisions.md`. The three supplied lobby documents provide product requirements, refined by the explicit user decisions recorded here. Source text and historical engineering observations must be reconciled with the current target checkout during detailed planning.

The framework store retains this existing change. Runtime handoff artifacts belong in the independent module at `specs/monopoly-game-lobby/`. Execution continues with the existing budget and prior evidence. The subsequent user requests narrowly authorize token-allocation repair and audited recovery from cycle-budget abandonment in the framework runtime. Other framework development, production service integration, final-art production, mainline commits, pushes and merges remain outside the requested rehearsal scope.

## Cycle-ceiling amendment — 2026-11-19

The user explicitly extended the same run to twelve total contract cycles, retaining all usage, configured models, the trusted overlay, frozen-test rules and independent review. Token ceilings remain 3,000,000 input / 900,000 output. The consecutive recovery starts at contract version 7 and preserves versions 1–6 and their abandonment evidence. Product requirements are unchanged.

## Explicit token amendment — 2026-11-19

The user approved total token ceilings of 6,000,000 input / 1,800,000 output while preserving every charge and reservation. The total cycle ceiling remains twelve. Apply the amendment only at a reconciled terminal boundary through a result-bound TokenRecoveryGrant. No product requirement, configured model, trusted overlay or frozen-test rule changes.

## Thirty-cycle continuation — 2026-11-19

The user explicitly authorized thirty total cycles and approved total token ceilings of 12,000,000 input / 3,600,000 output. Recover the actual version-twelve abandonment through the authenticated TokenRecoveryGrant into consecutive version thirteen. Preserve every earlier charge, uncertain reservation, model identity, contract, retained candidate and terminal record. Keep the trusted overlay, two-added-unit limit, independent judge, Red/global-freeze ordering and sequential Unity verification. Product scope and acceptance criteria are unchanged; human acceptance remains pending.

### Approved handoff scope clarification

The already approved fake match handoff replaces full playable in-match gameplay in this rehearsal. US-L3-10 retains complete lobby vehicle behavior and in-match equip rejection; actual walking/driving locomotion and dismount rendering remain a real-match integration disposition, not claimed execution. Preserve this disposition explicitly when exporting raw source clauses to test authors and judge. The source-required dedicated Shop entry is now supplied as serialized Lobby action `Shop`; its absence was a preparation defect, not an excluded requirement.

### Catalog disposition and visual verification allocation

The user explicitly chose "Use rehearsal catalog; defer production integration" for US-L7-11. Verify the game-owned catalog's complete fields and shared Appearance/Shop source; record production Luban/AssetGraph integration as deferred. Framework D-26 keeps visual fidelity and complete experience at candidate-bound human review. Retain automated functional/state/geometry/visibility/lifecycle checks and all 125 IDs; map qualitative transition fidelity and visual clutter to explicit pending review steps, without claiming automated visual acceptance or removing product requirements.
