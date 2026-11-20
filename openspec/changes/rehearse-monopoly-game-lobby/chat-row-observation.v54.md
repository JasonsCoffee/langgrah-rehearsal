# Explicit row identity and UI snapshot consumption

The actual cycle-53 dossier exposed two missing observation distinctions.
These declarations implement no rendering, events or service behavior.

## Prepared binding protocol

LobbyControlBinding now declares RowKind and RowEntityId. For the established
RowN bindings below Chat.Scroll.content, SHELL fills these from the actual data:

| Screen state | RowKind | RowEntityId |
|---|---|---|
| Private conversation list | conversation | actual peer synthetic account ID |
| Selected private history | message | actual delivered LobbyMessage.Id |

Other controls need no row metadata. Unused prepared rows are inactive. Every
active populated RowN under the content has the appropriate kind and nonempty
identity; fields are not a substitute for actual rendered content. The same
identity drives that row's runtime bindings and actions. No fixture may populate
these outputs, create history rows, or relabel a preview to make a test pass.

L13-11 can arrange distinct incoming/outgoing messages and another peer, collect
EVERY actual active bound RowN under Scroll.content, require message kinds and
the exact independently arranged message-ID set/count, and assert each label's
effective visibility and expected sender identity/text. Require zero active
conversation-kind rows in history. On actual Back require the populated peer-ID
set and rendered peer content again. Do not classify roles by whether a sender's
name happens to appear in a label. Metadata alone is insufficient: positive
dimensions, opacity, active state, clipping/viewport observations and displayed
message content remain required. Partially clipped scrollable history is valid.

## UI-origin snapshot observation

LobbyShellBindings now declares event
Action<string, LobbyUnread> UnreadSnapshotApplied. SHELL raises it only after
consuming the actual coherent shared Social.Unread snapshot to update the active
account's bound badges. It carries the actual applied snapshot, never a synthetic
test result. Service-internal reads do not emit this coordinator-owned event.
The existing service read/change observers remain unchanged for older tests.

L13-09 subscribes to this event to record actual UI-origin consumption, separates
fixture direct service calls from UI observation windows, delivers a real new
message, and verifies affected-account applied data AND currently visible C/tab
badge values before any navigation or extra fixture Refresh can mask a missing
live update. Test observers record only; they do not render, refresh or supply
snapshots. Retain shared-entry observations and expected counter values, but do
not treat an unattributed service-internal read as proof of UI acquisition.

All UI/service behavior is delegated; expected assertions against the prepared
nonfunctional baseline remain legitimate TDD. Correct maps to actual assertions.
