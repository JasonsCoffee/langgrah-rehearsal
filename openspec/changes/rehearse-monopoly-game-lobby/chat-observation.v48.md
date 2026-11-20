# Actual unread acquisition and action-linked transitions

The cycle-47 dossier is mandatory; every valid prior assertion remains.

## Nonfunctional prepared unread boundaries

LobbyWorld.UnreadSnapshotRead is an optional Action<string> observation callback.
SOCIAL invokes it exactly once whenever its actual Unread(accountId) entry reads
the shared snapshot. The callback returns nothing and cannot create unread data.
ILobbySocial/LobbySocial.UnreadChanged is an event carrying the affected account.
SOCIAL raises it after actual unread-affecting mutations, including delivery,
reads and pending friend-request changes. The declarations implement no behavior.

SHELL subscribes/unsubscribes with its lifecycle. The active account's badges use
one coherent shared Unread snapshot for each change, shared by Lobby/Chat entry
and channel badges. Quiet UI ticks do not start an independent unread polling
loop. Changing screens may acquire an initial shared snapshot. Do not require
zero queries across real changes, account switches or initial binding.

The named L13-02 test can record actual shared-entry reads without altering their
result, arrange changes through real Social methods and click real bindings.
Separate fixture's deliberate direct Unread calls from UI observation windows.
Require UI-originated shared-entry reads around actual binding/change, correct
badges from multi-peer data, and no quiet periodic acquisition after the update
settles while the UI clock advances. Event handlers used by the test may record
account IDs; they must not render badges, call Shell.Refresh or supply snapshots.
The test may advance the prepared UI clock and tick the real Shell.Refresh.
Delete invalid source regex/interface-count/arithmetic substitutes for this
oracle; preserve their effective unread outcome assertions elsewhere.

## Remaining presentation findings

- Opening/closing must cause a transition. Record the relevant actual view's
  pre-action state, click the actual action, inspect immediate state, advance the
  UI clock and tick the real shell, then inspect intermediate/completed state.
  Require a change correlated with that action and progression toward completion.
  Compare actual panel geometry/alpha or an action-linked animation state against
  the SAME relevant instance; do not accept an already-true/false parameter, any
  suitably named idle clip, normalized playback time or an unrelated Animator.
  Back may restore the Lobby view; inspect that actual restored presentation's
  collapse transition rather than a destroyed outgoing view. A particular
  AnimatorController is not required. The recording UI's stack lifecycle remains
  read-only. Runtime animation behavior is delegated to SHELL.
- L13-04: require overflowing populated scroll content, a real viewport mask and
  correct content/scroll geometry. Content rows outside the viewport are expected
  in a scrollable history: prove they are clipped, not that every history row fits.
  Do not skip rows classified as off-screen and then claim the whole layout fits.
  Inspect all populated row bounds, validate vertical ordering/non-overlap, and
  check clipping at the real mask boundary. Retain nonzero visible-row coverage
  and responsive font/avatar containment from v46.
- L13-05: for an already-friend peer, either no add icon OR an already-friend
  affordance is allowed. In both permitted presentations, forbid new requests,
  duplicate submissions and navigation/add effects. Requiring a particular
  visible already-friend overlay is an invalid stronger requirement.
- Preserve the fixed rendered truncation/expansion and self-avatar behavior.
  All fixture messages must remain within the configured 200-character limit.

Correct the current clause map. No source review implies Unity execution or
human visual acceptance.
