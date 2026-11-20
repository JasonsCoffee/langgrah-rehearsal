# Chat presentation: remaining preparation oracles

The actual cycle-45 dossier remains mandatory. Write assertions and input helpers
in the owned test partial; never implement service outcomes or rows in fixtures.
All five named methods must execute their clauses. Nonfunctional stubs should fail.

- L13-01: arrange enough successful world and private messages that each actual
  content rectangle exceeds its viewport. Respect cooldown and friendship.
  Set different nontrivial scroll positions, switch world/private/world/private,
  and verify both retained positions after genuine bound tab clicks. Require
  nonempty actual latest-message content. Observe opening AND closing animation
  behavior over time, rather than Animator/controller/parameter existence.
  World.UiClockSeconds is the prepared UI time input; SHELL can use it to drive
  the actual transition during Refresh, with Unity unscaled time as default.
  Observe real geometry, alpha or actual animation state progression; fixtures
  must never set an expected animated property themselves. Preserve pending
  qualitative human animation review. Do not require a particular controller.
- L13-02: prove prompt badge updates from the SAME world.Social aggregate used
  by the Lobby and Chat entry, with multiple unread peers and a partial decrement.
  Drive actual delivered-message notifications without advancing any polling
  clock and observe both entry badges. Comparing a total with its own sum or
  checking Social != null cannot establish the shared notification path. Retain
  the named-method 99+ boundary. Do not invent an independent test polling path.
- L13-03: after actual layout and TMP mesh calculation, require multiple rendered
  lines and an observable clipped/truncated long-message state. Click the actual
  expansion control; prove additional text becomes visible through rendered
  text/line geometry, not just overflowMode. Require visible own and peer avatars,
  names and opposite alignment. Attachment exclusion uses actual content roles.
- L13-04: arrange sufficient delivered rows with clock advancement. Require at
  least one actually inspected visible row. Measure capacity from the viewport
  and variable row extents. Change font and avatar sizes through real layout
  inputs, rebuild layout and prove row height changes while containing both.
  Never pass a loop that skips every row. The protected planning addendum below
  provides concrete coverage for the requirement-analysis section-6 table clause.
- L13-05: click the actual peer avatar to reveal its affordance, click its actual
  add control to submit active A -> B through the shared request entry. Observe
  RequestFriendInvocations before and after bound submissions and verify no
  duplicate pending request. Click the separately identified OWN avatar and
  assert no overlay, navigation, notification or friend-request change. Never
  silently return or substitute the peer avatar. Existing friends stay excluded.

## Rehearsal requirement-analysis section 6: QX13 addendum

This is a concrete derived planning record; original source documents remain
unchanged. The user explicitly approved the responsive chat layout below the
wallet bar, variable-height rows, scrollable history and input above the keyboard.

| Pending value | Rehearsal disposition | Evidence and final review |
|---|---|---|
| Rows per screen | No fixed numeric count. Derive visible count from the actual safe-area viewport below the wallet and above input, using each rendered row extent. | Named L13-04 measurements at the three approved portrait ratios; aesthetic proportion remains exact-candidate human review. |
| Row height | Recalculate from the larger avatar/text content extent plus actual layout padding; expanded text may require more height. | Named L13-04 changes font and avatar dimensions and checks responsive containment. |
| Final visual value | This adaptive rule is the approved rehearsal value; no invented universal 3–10 range. | Record observed candidate-bound counts with review evidence; visual approval is still the user's decision. |

The table clause is planning coverage through this protected source artifact,
not a reason to demand that an EditMode test edit the original requirements.
