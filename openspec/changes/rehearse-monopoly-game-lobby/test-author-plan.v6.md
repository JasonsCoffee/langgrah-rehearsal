# Focused final-cycle test authorship

The product requirements and full test selection are unchanged. The rejected
12-method presentation unit is split into core UI (8 methods) and NFR (4 methods),
with explicit historical ownership migrations and retained accounting lineage.
Use only this author's mapped source clauses. Do not copy the rejected tests.

## Core author: lifecycle and independent UI oracles

- Establish the active account through EnterAsync or ConfigureLobbyRehearsal.
  Navigating the recording adapter directly is fixture setup, not account login.
- Lifecycle truth table: an initial entry acquires Root/street once. Repeated
  Enter/Resume/OnLaunchRequest while already ready must not duplicate acquisitions.
  Leave releases the owned resources once; subsequent Exit/OnDestroy are
  idempotent. Re-entry after release acquires a fresh pair. Never demand a new
  load while the prior street is still owned, nor duplicate cleanup afterward.
- For the pending-entry race, prove the port was actually reached, the entry task
  is pending, and Leave invalidates that request before completing the gate.
  Complete the controlled gate and assert the specific cancelled/inactive outcome
  and exactly-once release of any late owned scene. Zero counters without these
  preconditions are not a race test. Cleanup must run even when assertions fail.
- Use GraphicRaycaster/EventSystem pointer dispatch to the actual rendered target
  for Outside, central display and foreground interception. Direct onClick.Invoke
  can test listener wiring but cannot establish hit-target behavior. The recording
  canvas must be active and layout updated before locating target screen points.
- Arrange appearance ownership explicitly before equipping a paid skin. Select
  the actions tab before action rows. Test model-tap cycling and playing animation
  states with actual updates, then re-enter and reacquire objects to test retained
  equipment/action. Never access destroyed scene objects or skip vehicle-none.
- FormatBalance boundary oracles must be independent literal values, including
  55999 -> 5.5万 and 129999 -> 12万. Exercise both coins and ingots independently
  with distinct values and verify the same formatter is actually used, rather
  than deriving expected UI text from the formatter under test.
- Check shared-wallet nested prefab provenance within the mapped wallet test,
  then check plus visibility on the actual navigated runtime views, not a fresh
  unbound clone. Its common source is SharedWallet_placeHolder.prefab.
- Marquee and MarqueeBadge belong to Lobby, not Chat. Opening World marks its
  unread messages read. Verify own delivered messages, arrivals while visible,
  actual label updates and dedicated badge placement without parsing message digits.
- Circular controls and Start prominence are runtime-view expectations: prepared
  placeholder images may be styled by the implementation. Check real geometry/
  hit shape and relative prominence, not merely action names or non-null images.
- The journey must arrange a genuinely populated nondefault partner page. The
  default recommendation cap is 20: either use a reachable page or explicitly
  increase the cloned Configuration.PartnerLimit before arranging more peers.
  Verify the row's actual peer identity, deep-link target, draft, selection, page
  and scroll values both before navigation and after return. Row0 exists in every
  prefab even with no data and cannot establish that a page contains a partner.

## NFR author: actual production boundaries

- Observe actual Root inputs/bindings and package.projectDefs.isPortraitStyle;
  do not construct uninitialized services. Count bindings for uniqueness. Measure
  safe-area geometry against the supplied pixel viewport at every ratio; unchanged
  geometry across all inputs must fail. Open a popup before proving its real
  canvas/camera order relative to the character, not just the recording canvas.
- Verify all ten actual VM/Presenter/View attribute constructor pairings. The
  INavigator and IUserDefault sources are supplied. Actual operations must be
  established, not unused dependency fields: inspect call instructions/call graph
  or exercise the real adapter with observation spies. If inspecting IL, resolve
  call/callvirt operands to the actual interface operations; mere type declarations
  do not prove use. Inspect all relevant implementation types for forbidden manual
  UI pooling/red-dot trees, while permitting ordinary active listener dictionaries.
- Arrange multiple private conversations and assert aggregate counts and visible
  updates after clearing each. Select the private tab before checking conversation
  rows. World read-on-open, own marquee delivery and the separate MarqueeBadge
  must be checked at their actual displays, including position. Digits in a name
  or message must not masquerade as a badge count.
- Switch A -> B -> A through the same session, then logout/re-enter. Use nondefault,
  distinct settings and observe actual audio/quality applications for both accounts.
  Isolate preference operations and enumerate every preference key touched; do not
  infer the preference boundary from arbitrary substring filters over fake-game
  state writes. Prove actual production IUserDefault read/write operations and
  account-prefixed preference keys. Preserve other accounts' settings and data.

## Verification and prompt accounting

Every mapped method needs nonempty stimuli and effective assertions. Correct the
coverage notes to describe the actual code. No skipped clauses, fabricated port
business state, invented controls/members, or optimistic repair prose. Behavioral
Red against unimplemented services is expected; fixture compile/setup errors are
not Red. Tests and their configuration freeze only after independent review and
real selected execution. Implementation prompts may omit unrelated test methods
and comments with exact source hashes; all helpers and mapped tests are retained.
Refactor prompts retain code/spec and frozen-test provenance rather than large
test bodies. The complete frozen selection still executes after refactoring.
