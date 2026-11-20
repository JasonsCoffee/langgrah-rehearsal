# Current focused repair and observable formatting boundary

This replaces the IL-specific repair approach in focused-repair.v7.md. Product
requirements, all 125 selections, independent review and frozen-test rules remain.

## Shared formatter observation

The prepared ILobbyEconomy / LobbyEconomy API now declares
`event Action<long> BalanceFormatted`. This is an observation-only seam. The
delegated ECON implementation must raise it exactly once for every actual
FormatBalance invocation. No functional formatter body has been supplied by the
Architect. Outside callers cannot raise a C# event on the economy instance.

For Story_L2_01, retain literal boundary outputs and distinct coin/ingot sentinels.
Subscribe to the SAME world's economy event, clear any trace from direct formatter
boundary tests, then stimulate actual UI binding/refresh with distinct balances.
Assert that both supplied amounts were formatted through that common instance and
that the correct labels display the independent expected values. Repeat with one
balance changed at a time. Do not let the test's own formatter calls populate the
UI trace. Do not use literal searches, interface-method counts or guessed IL.

## Remaining concrete version-seven findings

- NUnit Assert.DoesNotThrowAsync returns void. Never await that assertion's return
  value. Use runner-compatible async tests and correct NUnit assertion invocation;
  do not block player-loop-dependent tasks with GetResult or suppress arbitrary
  entry exceptions. Exercise real Monopoly Enter/Resume/launch after release AND
  repeated while live; exercise each real cleanup while live AND after release.
- Bind animation observations to the equipped CharacterMount instance. Verify its
  renderer is active, its layer is included in the relevant camera culling mask,
  its bounds intersect the frustum, and its projection lies in the intended central
  region. Assert the intended hit target, never pass null as expectedRoot merely
  to accept any GraphicRaycaster result. Verify Back reached Lobby before reopening.
- Force layout before computing pointer coordinates. Cover upper-right menu
  placement, marquee below the character region and badge placement. Keep the
  effective circular-hit, wallet, unread and populated-journey assertions.
- Update the actual C# and current acceptance map. A note claiming a repair while
  leaving its source unchanged is not an implementation. Other historical notes
  remain provenance, not current acceptance claims.
