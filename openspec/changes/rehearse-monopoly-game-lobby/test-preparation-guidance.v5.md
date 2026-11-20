# Verified preparation and observation guidance

This resolves implementation-readiness defects, not product acceptance reductions.
All 119 source stories and their non-overridden clauses remain required.

- The dedicated Tuanjie Editor compiler rejects `EditorSceneManager.OpenPreviewScene`
  with CS0117. Use `EditorSceneManager.OpenScene(path, OpenSceneMode.Additive)`
  and `EditorSceneManager.CloseScene(scene, true)` for owned test scenes. Track
  exactly which scene each fixture opened, preserve the prior active scene, do
  not save assets/scenes, and never close someone else's scene. Collect all scene
  observations before closing it; never return a destroyed Canvas or Transform.
- The actual street path is under `Runtime/Resource/monopoly/Scenes/LobbyRehearsal`.
  Prefabs/configuration are under `UI/Prefabs/LobbyRehearsal`. An absent target API
  is a fixture failure, not meaningful Red against business stubs.
- Lobby and Recharge now nest the same `SharedWallet_placeHolder.prefab`, with
  Coins, Ingots and Primary bindings. Inspect the actual loaded asset's nested
  prefab provenance to verify one wallet source; Object.Instantiate clones need
  not retain Editor prefab connections. Exercise data/plus visibility on runtime
  clones separately. Primary is the wallet plus in these two screens.
- Lobby has explicit `Outside` and `MarqueeBadge` bindings. Outside is a transparent
  full-area input target behind visible controls, initially inactive. The SHELL
  implementation must show it only while the menu is open, dismiss on its real
  pointer event, and preserve visible-button click handling. Test that actual
  event path; calling BackAsync is a separate back-path test, not an outside tap.
  MarqueeBadge is a separate noninteractive child with its own label; assert that
  label and its position. Never parse unread counts from sender/message text.
- The shared test harness is an observation-only adapter. Its active test canvas
  is a fixture setup obligation. Use the prepared private static font and avoid
  modifying shared font/material assets. Verify actual visibility only after the
  fixture has established an active parent; do not claim inactive parents activate
  automatically. Test canvas setup is not evidence of production Root layering.
- The v5 harness API adds AudioCalls, QualityCalls and lifecycle observations.
  Implement them only by recording actual adapter method calls. Do not compute or
  assign coordinator/business outcomes. LastScreen records navigation history;
  use the actual current view/context to test Back, or faithfully record Back's
  displayed view. An adapter must not automatically unload a previous street in
  LoadStreetAsync: that masks missing coordinator cleanup. Reject overlapping
  loads and record real method ordering. Only owned fixtures are disposed.
- Use opposite sentinel audio values or actual call counts when proving restored
  false preferences; default-false fields alone are vacuous. Clear/partition fixture
  seeding logs before settings stimuli. Preference keys must start with the active
  synthetic account ID; do not apply that preference-boundary assertion to unrelated
  fake-game state or another seeded account. Verify production IUserDefault usage
  in its actual adapter source separately from the in-memory persistence fake.
- Concrete VM sources are supplied. Each `XVM` has
  `[ViewPresenter(typeof(XPresenter))]`; each presenter has
  `[RequireView("monopoly", typeof(XView))]`. `CustomAttributeData` constructor
  arguments provide an exact reflection oracle without guessing attribute property
  names. Verify all ten pairings and inspect all relevant implementation partials
  for prohibited pooling/storage mechanisms rather than only one filename.
- The actual package.json and MonopolyRootScene.cs are supplied read-only. The
  package's `projectDefs.isPortraitStyle` is true; Root's
  code configures reference resolution 1080x2160, AdaptMode.Expand and UI camera
  layer 200 with paired restoration. Observe these authoritative inputs and the
  real Root binding. Never construct an uninitialized SystemInfoService or guess
  whether an unknown property is static. Rendering order and hit targeting need
  corresponding real canvas/camera or pointer observations, not port counters.
- For an enter/exit race, use controllable pending UniTasks in a test-local
  ILobbyEntryPort decorator forwarding to the real fixture. Assert the real pending
  ordering/cancellation result and resource ownership. A sequence of synchronously
  completed calls establishes ordering only. Verify bind-twice/single effect,
  unbind/no effect and no remaining session subscriptions after shutdown/destruction.
- Reacquire character/vehicle/animator instances after scene transitions. Equip an
  actual non-null vehicle definition rather than skipping vehicle-none. Observe
  current animation state after an appropriate update rather than only clip names
  or the numeric Action parameter. Do not read destroyed pre-transition objects.
- Deliver a new world message through the fake chat service or an explicit
  application update/refresh, then assert visible chat and marquee updates. Direct
  mutation of a plain List does not itself notify UI. Use adversarial digit-bearing
  sender/message text to ensure badge assertions target the dedicated badge.
- Every assertion and checklist claim must describe what the code actually
  exercises. No invented members, missing imports, disabled tests, conditional
  coverage skips, fabricated fixture business behavior or optimistic repair prose.
  A truthful smaller checklist does not waive any mapped acceptance clause.
