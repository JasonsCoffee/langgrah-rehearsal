# Pending lobby review guide

This is preparation, **not a human review request**. Candidate
`73816996becb75eb390b0625f69c67ca630774f7` is still undergoing native
verification. Green, Refactor, final verification and a candidate-bound review
request remain required. If the candidate changes, this guide must be rebound
to the actual requested revision before review. No acceptance is recorded.

## Launch when the native review request is ready

Use the dedicated Unity host selected by `UNITY_HOST`. Enter Play Mode and use
the existing **Monopoly Game/Scene** entry. The expected result is the original
Western street geometry, 3D character and vehicle, lobby navigation, wallet and
five tiers. Returning opens the simulated platform home; “重新进入大赢家” uses
the same entry again.

To open the implemented rehearsal controls, select this asset in the Project
window:

`Assets/JJGame/monopoly/Runtime/Resource/monopoly/UI/Prefabs/LobbyRehearsal/Art/LobbyConfiguration_placeHolder.asset`

In its Inspector, click **Open Lobby Rehearsal**. The current source supplies
this custom Inspector and window. The separate prepared Editor panel shell is
not the implemented control window. Use the window in Play Mode to switch
synthetic accounts, advance the fake server clock and drive peer world messages,
invitations, acceptance and disconnection. It also exposes fake payment outcomes
and reconciliation. These launch instructions are derived from the current
candidate source; they still require actual candidate review.

## Acceptance interactions

1. Enter, exit and re-enter repeatedly. Check camera and UI cleanup, the fake
   platform route, account identity, wallet, tier selection and every menu page.
   Tap the central 3D region for appearance settings; visible buttons must handle
   their own clicks. Chat opens from the smiley shortcut; Invite teammate opens
   the Friends cooperation-partner tab.
2. Change skins, vehicles and Idle/Wave/Celebrate. Check eligibility, acquisition
   routes, equipped markers and immediate previews. Advance the fake clock beyond
   an equipped item's expiry: an eligible default and brief notification should
   appear. Reopen Shop to check descending priority, ascending ID ties and owned
   items last; an open Shop should retain its ordering.
3. Exercise fake purchase, exchange and card flows, including paid, cancelled,
   failed and repeated reconciliation outcomes. Check one-time credits, sufficient
   funds, saved state and card accrual after clock advancement or a Play Mode
   restart. Monthly/annual durations are configured as 30/365 days. Re-purchase
   extends validity from the later of current expiry and fake time. VIP remains
   informational and does not discount entry fees.
4. Use two or more synthetic peers for invitations, expiry and acceptance races.
   Check the configured 30-second expiry, first successful acceptance, automatic
   closure of other invitations and “队伍已满” for in-flight full-party acceptance.
   Both members can change the shared tier, start or cancel queueing. Cancellation
   preserves party/tier; both balances are checked and fees are charged at start.
5. Advance queue time to the configured 30-second timeout. Inspect 24 handoff
   seats, factions, fees and bot balances. Disconnect/reconnect a peer and check
   the same seat/party with temporary AI control. Confirm abandonment, “已放弃”,
   retained fee and refusal to rejoin. Use “完成模拟对局” and check deterministic,
   one-time settlement plus history/ranking updates before returning to the lobby.
6. Check friend search by the same synthetic platform ID used for display/copy
   and invitations, the configured 100-friend cap and seven-day request expiry.
   Check recent partner/opponent lists and their configured 20-entry limits.
7. Send world and private chat. Check the three-second world cooldown and
   “发言过于频繁”, 200-Unicode-character limits with rejected drafts preserved,
   world/private separation, variable-height history, own avatar on the right
   and the input above the keyboard. Opening World marks visible/new world
   messages read; the marquee retains the latest delivered world message,
   including the player's own. Long-press → 举报 → confirmation should record
   the fake report and show “举报已提交”. Check separate private/world/request
   unread counters.
8. Check rolling 24-hour/seven-day rankings at one shared fake timestamp, ten
   ranked rows plus pinned self, history expansion/collapse and visible journal
   details inside scrolling/clipping bounds. Abandoned expenses equal income
   plus entry fee. Check Settings, account-persisted sound/quality overrides,
   simulated support and return paths.

The full mapped story scope remains authoritative; these are review journeys,
not a replacement for its individual acceptance clauses.

## Visual and device checks

Use portrait ratios **9:16, 1:2 and 9:19.5** from the current review rubric.
Inspect readable Chinese text, safe areas, layering and every page/back route.
Repeatedly change previews and scroll appearance lists: no flashes, blank cells,
stale models, duplicates or unintended occlusion should appear. Inspect Shop
tabs and insufficient-funds routes for unused promotional cells or source/debug
navigation clutter. Check actual device keyboard activation with click, typing,
pasting and submission in Friends search and Chat. EditMode keyboard intent
evidence does not establish physical device presentation.

## Evidence and limits

The complete 199-file test/configuration freeze remains
`2da65db6815d61fb277a19f826b4d512e78c8bc4dc2f4f8c4d1b3387e8d1c520`.
The current candidate's selected results are pending. Previous candidate results
are history, not evidence of this candidate passing. The progress and verification
reports identify actual receipts and pending gates.

Art is original placeholder geometry. Platform, support, purchases, chat,
moderation and match services are rehearsal fakes. Production Luban/AssetGraph
integration is explicitly deferred. Full playable-match movement, rent and driving
are outside the approved handoff rehearsal. Visual acceptance belongs to the
user reviewing the exact requested candidate; automated Green does not approve it.
