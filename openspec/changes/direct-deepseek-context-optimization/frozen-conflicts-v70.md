# Candidate-bound frozen acceptance conflicts

Candidate `625db77bf4e75060435947d955328a729f6f87dc`, contract 70
`bbbfcf9dc2b51f1ffb9d8a935a1fbb72ca148ada5c2a89f6b37752065f9315e7`.
Actual step10 execution: 129 executed, 39 passed, 90 failed, zero skipped;
mixed assertion/runtime evidence is nonbehavioral. No Green or acceptance.

Judge (GPT-6.1 Sol, low) returned a genuine `contract` finding for ECON in
`judge-v70-step10-verify-ECON`. Its exact native effect and SDK receipt remain
authoritative. Architect source inspection independently confirmed two conflicts.
The optimizer retained the full 2,600,596-byte packet because its 2.39% packing
reduction was below the 20% threshold; no paid selector hid either assertion.

## 1. Recharge wallet plus

- `Tests/Runtime/Script/LobbyRehearsal/LobbyPresentationNfrTests.cs:162`
  applies `AssertSafe(view, "Primary", ...)` to every screen, including Recharge.
  `AssertSafe` at line 557 requires the same button active, visible and unclipped.
- `LobbyPresentationCoreTests.cs:778` requires Recharge Primary inactive.
- `LobbyEconomyRechargeTests.cs:360` also requires Recharge Primary inactive.
- Original user story US-L2-02 explicitly omits the plus inside Recharge; the
  frozen runtime spec repeats this at `specs/monopoly-game-lobby/spec.md:63`.

Proposed delegated test correction: retain all three viewport/safe-area cases,
keep Coins and Ingots measurable and visible on Recharge, explicitly assert the
Recharge plus remains hidden, and retain Primary safe-area checks on screens
where it is required. No geometry, clipping, rendering or other screen coverage
is removed. This changes the NFR assertion to the documented screen semantics.

## 2. Ranking initial tab

- `LobbyPresentationCoreTests.cs:509` maps the ranking menu row to `day`.
- `LobbyRecordsSettingsTests.cs:106` sends the same menu action but requires
  `week`. Its explicit day/week switching and independent scroll assertions agree
  with its weekly default.
- `specs/monopoly-game-lobby/binding-protocol.v2.md:10` also says day ranking.
- Original US-L5-01 explicitly defaults to the weekly ranking. The user's rolling
  24-hour/seven-day window decision changes aggregation windows, not this default.

Proposed delegated test correction: align the core menu-route assertion with
`week`, preserve explicit Tab0/day and Tab1/week checks and all independent scroll
and snapshot assertions. Architect would align the conflicting protocol clause
and make the source-backed default explicit in the next contract's specification.

## Required authorization and safeguards

No current or prior frozen file has been edited. The latest user instruction
requires preserving frozen tests, so this report is a concrete proposed scope
revision, not authority to implement it. If authorized, a new consecutive contract
cycle must delegate the affected test-source corrections to Coder, obtain actual
independent Judge approval, execute valid Red, then establish a fresh global
freeze before implementation. Keep all previous candidates, original frozen
bytes, evidence, usage/reservations, models, aggregate ceilings and overlay.
Do not handwrite assertion repairs or reinterpret these contradictions as game
implementation failures. Other genuine implementation failures remain in scope.
