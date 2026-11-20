# Functional verification and candidate-bound visual review

Authority: frozen framework decision D-26, `docs/decisions.md`: "EditMode results
cannot prove visual fidelity or complete experience." The final gate is an
authenticated human inspection of the exact candidate. Automated Green offers
`awaiting_human_review`; it never accepts the feature.

The previous authoring instructions overclaimed that every qualitative visual
clause must be proved by an EditMode pixel oracle. Correct that verification
allocation while retaining every product requirement and all 125 test IDs.

Automated tests must still prove interactions, independent expected values,
nonempty data, item identity, active/visible geometry, appropriate camera and
projection, selection versus using state, lifecycle/subscription cleanup,
immediate equipped-instance replacement, transaction/race behavior, persistence,
time boundaries and account isolation. Retain effective assertions. Merely
calling a method, matching a field name, inspecting inactive UI or comparing a
value with itself never counts as coverage.

These qualitative checks belong to the exact candidate's pending human visual
rubric, in addition to automated state/geometry assertions:

- V1 / US-L3-02 and US-L7-03: repeatedly change preview selection and actions;
  observe the final displayed character/vehicle composition for smooth changes,
  black/white flashes, stale models and occlusion. Endpoint and isolated-camera
  pixels are not claimed as complete visual evidence.
- V2 / US-L3-03: scroll a populated appearance list in both directions at the
  three portrait ratios; check actual thumbnail continuity and absence of blank
  frames. Automated tests still establish matched visible rows, nonempty data,
  scrolling and clipping/geometry.
- V3 / US-L7-10: inspect the actual shop for unnamed noninteractive promotional
  placeholders and visual source-navigation clutter. Automated tests still
  establish exact products/prices, allowed functional controls and their routes.
- V4: inspect the original Western 3D placeholders, equipped appearance, vehicle,
  Idle/Wave/Celebrate, popup ordering and readability at 9:16, 1:2 and 9:19.5.

Before freeze, delegated authors may replace demonstrably invalid pixel-sampling
assertions identified in the actual dossier with sound mechanical observations
and an explicit link to V1/V2. They must preserve functional assertions and must
not label pending human checks as automated passes. The independent judge must
review the resulting automated coverage and truthful clause-level disposition.
No model can complete or approve V1–V4 for the user.

This policy does not defer functional work or require less than a working lobby.
The user separately answered "Use rehearsal catalog; defer production
integration" for US-L7-11. Verify the game-owned rehearsal catalog's complete
fields, exact products and shared data source; record production Luban/AssetGraph
integration as explicitly deferred. The approved handoff-scope disposition in
version 15 continues unchanged.
