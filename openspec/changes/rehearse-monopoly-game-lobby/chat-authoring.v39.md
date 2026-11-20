# Focused Chat authoring and approved precedence

These are test-author units. Arrange inputs through the actual prepared fake
services, drive real bound UI, and assert the specified observable outcomes.
Those assertions should fail against nonfunctional production stubs. Writing
assertions is not implementing game business behavior. Recording/input helpers
must not manufacture service results, expected notifications or rendered rows.

The fourteen mapped methods are partitioned into five presentation/avatar tests,
four message-validation/delivery tests, and five conversation/state tests. All
eighteen existing test-method bodies, including four unmapped companions, are
preserved byte-for-byte before delegation. Required assertions must execute in
the contract-named methods; unmapped companion methods receive no acceptance
credit. Consolidate their effective checks into the mapped tests without calling
NUnit test methods as helpers. Exclusively reachable helper bodies move verbatim
with each focused scope; shared helpers remain with the primary Chat author.
The message author runs first to repair its exclusive input-focus helper. Each
author may add distinct observation/input helpers in its own partial.

## Explicit user override

The user expressly answered: "Yes, follow the original mockup and show my avatar
beside my right-aligned messages." The approved exported proposal and runtime
spec already require the player's messages AND avatar to align right. This
overrides US-L13-03's older no-self-avatar text, which remains unchanged in the
original source export. The cycle-38 judge repeated that older exclusion; it is
not authoritative over the user's decision. Both own and peer avatars must be
actually visible. Clicking one's own avatar has no add-friend effect. Preserve
all other original clauses and user-approved overrides.

Chat capacity follows actual viewport and variable-height rendered rows below
the wallet bar, not an arbitrary three-to-ten range. Populate content and measure
clipping, wrapping, expansion and scroll behavior across the approved ratios.
Arrange distinct world/private scroll positions and actual latest delivered
world-message content, including the player's own message. Never compare a
field with itself or use an empty string as a latest-message oracle.

## Prepared fake-delivery input

World.ChatDeliveryAllowed is now a declared optional Func<LobbyMessage,bool>.
SOCIAL invokes it after validation and before actual message commit; null allows
normal fake delivery. False simulates failure, commits no message, and returns
localized failure feedback. This input implements no service behavior. SHELL
disables the send control while the real delivery call is in progress and restores
it on completion. A recording gate may observe the actual bound button during
that call and return true/false; it must not change UI state or deliver messages.
Observe the bound click's own outcome, rather than calling SendWorld a second
time and accidentally testing cooldown instead. Preserve failed/overlong drafts.

Advance fake time between successful world sends when arranging multi-message
fixtures. Private messages still require current friendship. Exercise Unicode
limits for both channels, cooldown at configured boundaries, successful delivery,
explicit rejection feedback, and long-press report confirmation/cancellation.
Keyboard-request intent is automated through the declared callback; physical
keyboard presentation remains the explicit device-review check.

Correct the actual TMP input event signature and use genuine bound input events.
Use account-partitioned notification observations. Keep all source clauses in
truthful current maps; do not infer compilation or execution from source review.
