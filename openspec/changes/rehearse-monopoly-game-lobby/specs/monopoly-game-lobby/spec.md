# Lobby rehearsal specification

## Purpose

Provide a complete, reviewable Monopoly client lobby with original 3D presentation and deterministic fake platform/game services, using the approved rehearsal decisions and existing game entry.

## ADDED Requirements

### Requirement: Existing entry and platform return

The lobby SHALL use the existing Monopoly Game/Scene entry, framework Root lifecycle and VVMP navigation for fake platform entry, resume, exit and re-entry.

#### Scenario: Enter and return

- **WHEN** the existing game entry is invoked
- **THEN** the 3D lobby opens through the Root/Navigator route
- **AND** the top-left return immediately opens a simulated platform home whose “重新进入大赢家” action uses the same entry

#### Scenario: Release and re-enter

- **WHEN** the player exits and re-enters repeatedly
- **THEN** camera, subscriptions and UI lifecycle resources remain paired and the configured fake account state is restored

### Requirement: Original 3D presentation

The lobby SHALL present a fully 3D Western-style street with original placeholder character and vehicle geometry, prepared scene/prefab references and Idle, Wave and Celebrate preview actions.

#### Scenario: Inspect and animate the preview

- **WHEN** the lobby and appearance previews are opened
- **THEN** real 3D geometry renders with the equipped skin and vehicle
- **AND** the lobby central display region opens appearance settings while visible controls handle their own clicks
- **AND** appearance-model taps cycle the three prepared actions

### Requirement: Portrait navigation and safe areas

The lobby SHALL retain 1080 × 2160 portrait adaptation, safe-area layout, contextual menu and caller-aware return routes using framework routing.

#### Scenario: Use the lobby controls

- **WHEN** the player opens the menu or either bottom circular button
- **THEN** the menu exposes Friends, Rankings, History, Shop, Settings and Chat
- **AND** the smiley opens Chat and the second circular button opens Invite teammate on the cooperation-partner tab

#### Scenario: Resize and return through a deep link

- **WHEN** the viewport uses 18:9, 19.5:9 or 20:9 or the player returns from a nested screen
- **THEN** essential controls remain within safe areas and the correct caller, selection and applicable scroll position are restored

### Requirement: Wallet and synthetic identity

Fake platform data SHALL supply one synthetic account ID and configurable initial balances of 10,000 coins and 200 ingots. Display, copy, lookup and invitations SHALL use that ID.

#### Scenario: Display boundary amounts

- **WHEN** either balance is 0, 9999, 10000, 19999, 99999, 100000 or 129999
- **THEN** one shared formatter applies the documented truncation rules, including 55999 → 5.5万 and 129999 → 12万

#### Scenario: Open the appropriate recharge tab

- **WHEN** the player taps coins, ingots or the lobby wallet plus
- **THEN** the corresponding exchange or ingot tab opens
- **AND** the recharge wallet hides its plus control

### Requirement: Appearance catalog and ownership

A game-owned configurable catalog SHALL define six skins, four vehicles and the no-vehicle option. A fake appearance service SHALL manage account unlocks, expiry and equipment.

#### Scenario: Preview and equip

- **WHEN** the player opens appearance, changes selection or confirms equip
- **THEN** skin/vehicle tabs, fixed-frame catalog thumbnails, selected/using indicators and 3D previews reflect their distinct states
- **AND** eligible equipment updates the lobby immediately while locked items offer a shop deep link
- **AND** initial defaults follow the documented eligible gender/default-pool rules and remain stable for that account

#### Scenario: Expire equipment

- **WHEN** an equipped timed item reaches its seven-day configurable expiry using fake server time
- **THEN** an eligible default immediately replaces it and a brief notification appears
- **AND** remaining-duration text rounds upward using hours below one day and days otherwise

### Requirement: Shop ordering and purchase

The shop SHALL provide configurable direct coin purchases, confirmed transactions and acquire/equip deep links for skins and vehicles.

#### Scenario: Open and buy

- **WHEN** the shop opens
- **THEN** eligible unowned products sort by shopPriority descending and id ascending, followed by owned products
- **AND** permanent/seven-day skin prices are 1000/300 and vehicle prices are 3000/900

#### Scenario: Confirm or recover a purchase

- **WHEN** a purchase is confirmed, cancelled, repeated or rejected for insufficient coins
- **THEN** confirmed debit/ownership changes occur once, cancelled or failed operations retain consistent balances, and the insufficient-coins route offers exchange
- **AND** successful purchases offer immediate equip, with the appropriate appearance tab
- **AND** item order changes when the shop is reopened and remains stable during the open session

### Requirement: Configured tiers and selection

The tier carousel SHALL use configured base values 10, 50, 250, 1000 and 5000 with configurable multiplier 10, supporting a configured number of tiers and per-account selection memory.

#### Scenario: Select and restore a tier

- **WHEN** tiers are selected by swipe or side-card tap, or the account is reopened
- **THEN** the centered card snaps to selection, first/last boundaries hold, and remembered valid selection is restored
- **AND** new accounts and removed remembered tiers select the first tier

#### Scenario: Recalculate affordability

- **WHEN** tier, wallet or party membership changes
- **THEN** fees of 100, 500, 2500, 10000 and 50000 are recalculated from configuration
- **AND** insufficient balance changes the primary action to “金币不足” with the documented recharge route

### Requirement: Party and invitation arbitration

The fake match service SHALL support leaderless two-player parties, synchronized tiers, configurable 30-second invitations and atomic acceptance arbitration.

#### Scenario: Accept competing invitations

- **WHEN** a player successfully accepts an invitation
- **THEN** that acceptance determines their party and closes their other invitations
- **AND** the party filling closes the inviter's other invitations while acceptances already in flight receive “队伍已满”

#### Scenario: Change a party

- **WHEN** either member changes tiers or starts matching
- **THEN** the tier and fee synchronize to both players and the service validates both balances before queueing
- **AND** a teammate removal uses the documented two-step avatar action and returns the two-player party to single-player state
- **AND** matching must be cancelled before leaving the party

#### Scenario: Invite an ineligible peer or expire an invite

- **WHEN** a busy, offline or cross-game peer is invited, or the deadline passes
- **THEN** the documented in-game eligibility feedback applies and expired invitations cannot create a party

### Requirement: Queue start and cancellation

The fake matcher SHALL use a configurable three-second heartbeat, 24 seats and a configurable 30-second deadline, with per-player fees charged once at match start.

#### Scenario: Start with available players or fill the queue

- **WHEN** a heartbeat finds 24 players or the 30-second deadline is reached
- **THEN** the match starts once, filling remaining seats with fake bots at the deadline
- **AND** each bot has a synthetic in-match balance equal to the tier fee and party members occupy the same faction

#### Scenario: Cancel a party queue

- **WHEN** either party member cancels before match start
- **THEN** both leave the queue with party and selected tier preserved and their fees uncharged

#### Scenario: Validate start atomically

- **WHEN** balances or party validity change during the start request
- **THEN** final validation either commits all member debits and seats once or rejects the start with a consistent state

### Requirement: Handoff and disconnected seats

Successful matching SHALL open a handoff view with tier, charged fee, 24 seats and faction assignments, preserving reconnectable disconnected seats.

#### Scenario: Disconnect at match entry

- **WHEN** a peer disconnects as entry completes
- **THEN** the seat and party assignment remain, temporary AI control is simulated and the player can reconnect to that seat

#### Scenario: Inspect the match

- **WHEN** the handoff view opens
- **THEN** it displays the committed tier, fee, full seat list and factions
- **AND** new entrants are rejected after start

### Requirement: Abandonment and simulated completion

The fake match service SHALL supply confirmed abandonment and deterministic completion with durable one-time wallet settlement, history and ranking updates.

#### Scenario: Abandon a match

- **WHEN** return-to-lobby is requested and abandonment is confirmed
- **THEN** history records “已放弃”, the fee remains charged, profit equals negative entry fee and expenses equal income plus entry fee
- **AND** the abandoned seat cannot rejoin that match while reconnectable disconnected seats retain their separate policy

#### Scenario: Complete a simulated match

- **WHEN** “完成模拟对局” is invoked or its result is retried after restart
- **THEN** one deterministic result settles the wallet once, updates history and rankings and returns to the lobby

### Requirement: Platform friends and recommendations

The fake platform SHALL supply friend relations, presence, a configurable 100-friend limit and seven-day unanswered-request expiry. Game recommendations SHALL retain up to 20 historical partners and 20 qualifying opponents.

#### Scenario: Browse and mutate friends

- **WHEN** the player pages, copies/searches an ID, sends/responds to a request or deletes a friend
- **THEN** empty, missing-ID, self-ID, full-list, page-boundary, confirmation and failure states follow the source acceptance clauses
- **AND** duplicate requests are idempotent, page-local sent state resets on reopening, and expired requests disappear using fake server time

#### Scenario: Build recommendations

- **WHEN** match-result fixtures contain previous non-friend teammates and top-three opponents
- **THEN** documented eligibility, recency, source-priority merging and configured limits apply
- **AND** existing friends are excluded and platform relations remain separate from game history

### Requirement: Rolling rankings and pinned self

Rankings SHALL aggregate documented positive income over rolling 24-hour and seven-day windows using a shared fake-server snapshot, with ten ranked rows and a pinned self row.

#### Scenario: Refresh the two rankings

- **WHEN** a snapshot is requested
- **THEN** both windows use the same timestamp, positive income excludes expenses, ties follow achievement time and results are stable for that snapshot

#### Scenario: Page and inspect self

- **WHEN** ranking pages or tabs change
- **THEN** a pinned self row remains visible independently of ten-row pages, loading ends at rank 100 and an out-of-range/new account displays 100+
- **AND** each tab preserves its scroll state and the first three ranks use medal styling

### Requirement: History and shared result data

History SHALL display supplied results newest-entry-time first, with final placement, profit and expandable income/expense totals from the same result data used by rankings and the rehearsal result detail.

#### Scenario: Inspect a result

- **WHEN** a history row is expanded
- **THEN** it shows income and expenses including entry fee, closing the previously expanded row without reordering
- **AND** completed rows show the service's final rank while abandoned rows show “已放弃” in the rank column

#### Scenario: Reconcile totals

- **WHEN** completed and abandoned fixtures are inspected
- **THEN** displayed totals agree with the supplied income entries, cash/profit and approved abandonment accounting
- **AND** detailed result income agrees with the ranking source data

### Requirement: Responsive world and private chat

Chat SHALL provide world and friend-only private text channels below the wallet bar, with variable-height rows, scrolling and keyboard-safe input.

#### Scenario: Render and navigate conversations

- **WHEN** channels or private peers change
- **THEN** the documented list/conversation/back routes and per-channel positions are preserved, the player's messages and avatar align right and other players' align left
- **AND** plain text is escaped and the input remains above the keyboard

#### Scenario: Validate and send text

- **WHEN** a blank, over-200-character or too-frequent world message is sent
- **THEN** the fake service rejects it with explicit feedback and preserves the draft
- **AND** a configurable three-second per-player world cooldown gives “发言过于频繁”
- **AND** the configurable 200-Unicode-character limit also applies to private messages

#### Scenario: Lose private-message eligibility

- **WHEN** the recipient is a non-friend or is removed from friends
- **THEN** private sends are rejected with feedback while existing history remains readable

### Requirement: Reporting and shared unread state

One shared service SHALL expose distinct world, private and pending-request counters and record confirmed message reports.

#### Scenario: Read world and private messages

- **WHEN** World chat opens or receives messages while visible
- **THEN** those world messages are read and the marquee retains the latest delivered world message including the player's own
- **AND** opening a private conversation clears that peer's unread count and updates the aggregated private total

#### Scenario: Report and aggregate independently

- **WHEN** a message is long-pressed and 举报 is confirmed
- **THEN** the fake moderation service records it and displays “举报已提交”
- **AND** world unread, private unread and pending requests retain separate counters without double counting

### Requirement: Simulated checkout and exchange

The fake platform SHALL expose configurable six-tier ingot purchases and exchanges, atomic balances and idempotent order/callback handling.

#### Scenario: Purchase or exchange

- **WHEN** a documented tier is selected and confirmed
- **THEN** prices 3/20/50/100/200/500 purchase 30/200/500/1000/2000/5000 ingots, and those ingot amounts exchange for 3000/20000/50000/100000/200000/500000 coins
- **AND** simulated payment cancellation returns to the caller and duplicate callbacks deliver once

#### Scenario: Purchase ingots to complete an exchange

- **WHEN** an exchange requires additional ingots
- **THEN** the documented confirmation offers simulated purchase followed by automatic exchange
- **AND** a later exchange failure preserves the successful purchase and offers explicit recovery without silent loss

### Requirement: Coin-card entitlements and accrual

The fake platform SHALL persist configurable 30-day monthly and 365-day annual cards with the approved complete base reward schedule and exactly-once catch-up.

#### Scenario: Purchase a card

- **WHEN** monthly, golden annual or diamond annual is purchased
- **THEN** simulated prices are 30/298/998, purchase grants are 15000/180000/500000 coins, and scheduled grants are 1500 daily/1500 daily/20000 weekly
- **AND** that base schedule is the complete entitlement

#### Scenario: Extend and accrue

- **WHEN** a card is repurchased or fake time advances across grants, expiry or a closed-lobby interval
- **THEN** validity extends from max(expiry, now), first grants are due after 24 hours or seven days, and the existing cadence continues through expiry
- **AND** every due grant is credited once and restart/retry preserves that result

### Requirement: Informational platform VIP

The fake platform SHALL supply VIP qualification from six-month recharge data, with immediate upgrades and first-of-month re-evaluation. The client SHALL display informational benefits while entry fees retain the configured values.

#### Scenario: Inspect VIP and rules

- **WHEN** VIP=0 or levels 1–7 and their rules are viewed
- **THEN** default selection, lock state, progress, grade boundaries and the documented VIP=0 exchange route follow the supplied data
- **AND** the original benefit categories use original Monopoly-specific rehearsal descriptions

#### Scenario: Re-evaluate qualification

- **WHEN** recharge or a first-of-month boundary changes qualification
- **THEN** the fake platform uses the latest six-month period in Asia/Shanghai and supplies the resulting VIP state to the client

### Requirement: Settings and simulated support

Settings SHALL provide account-isolated music/effect controls, framework quality selection, rules/about and a simulated support destination.

#### Scenario: Change and restore settings

- **WHEN** a setting changes or the account changes
- **THEN** audio controls apply independently, Low/High map to the lowest/highest supported framework tiers, and device rating supplies the initial default before a saved account override

#### Scenario: Read help and information

- **WHEN** rules, about or support is opened
- **THEN** rich-text rules scroll, about shows the real build version, and simulated platform support shows rehearsal help with a return to Settings
- **AND** the reusable settings screen receives its in-match exit context through the documented framework pattern

### Requirement: Durable account and time isolation

Fake-service balances, purchased appearances, equipment and card entitlements SHALL survive Play Mode restarts per synthetic account. Timestamps SHALL be stored in UTC with Asia/Shanghai calendar boundaries.

#### Scenario: Restart and switch accounts

- **WHEN** Play Mode restarts or another synthetic account is selected
- **THEN** the correct account's service data and local preferences are restored without reading or clearing another account's state

### Requirement: Editor rehearsal controls

An Editor panel SHALL switch synthetic accounts, advance fake server time and drive peer events while the active account stays logged in.

#### Scenario: Exercise time and peers

- **WHEN** the reviewer advances time or injects a peer message, invite, acceptance or disconnection
- **THEN** the same application service paths used by normal UI interactions process those events and update the visible lobby state

### Requirement: Frozen verification and human review

The trusted host SHALL preserve the current run budget and overlay identities, freeze tests before delegated implementation and offer only an exact fully verified candidate for human review.

#### Scenario: Prepare and run the candidate

- **WHEN** implementation is dispatched
- **THEN** a validated contract, imported frozen presentation, independently reviewed tests and behavioral Red evidence exist
- **AND** configured coder/judge calls use the existing persistent budget and Unity selections run sequentially with baseline/import drift checks

#### Scenario: Offer human review

- **WHEN** Green, Refactor and the complete declared integrated suite pass
- **THEN** the run reaches awaiting_human_review with exact candidate, acceptance behaviors, launch instructions, test results and visual-review limits

### Requirement: Source acceptance and traceability

The rehearsal SHALL cover all applicable source-story acceptance clauses, with approved proposal decisions taking precedence for this rehearsal. Server responsibilities SHALL be represented by fake-service acceptance and in-match gameplay by the approved handoff/result fixtures.

#### Scenario: Verify complete coverage

- **WHEN** acceptance tests and the runtime contract are prepared
- **THEN** every one of the 119 source stories and 143 functional IDs has an explicit disposition and mapping to actual tests
- **AND** US-L4-07 is verified as the documented cross-game invitation exclusion
- **AND** approved overrides and shared journeys remain traceable through independent review and execution receipts
