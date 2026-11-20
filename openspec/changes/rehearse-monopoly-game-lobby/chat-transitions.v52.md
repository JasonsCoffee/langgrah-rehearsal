# Replace two ineffective proxies with actual controlled observations

The actual cycle-51 dossier remains mandatory. Preserve every effective outcome
check and cross-partial signature. The two rejected proxies are not effective
assertions to preserve unchanged.

## L13-01: observe animated presentation, not unrelated Animator activity

DELETE the helper route that combines an Open/Show parameter with arbitrary
state/normalized-time progression. Do not retain a required AnimatorController,
clip name, parameter name or unrelated Lobby Animator signature. Those are
implementation-specific stronger requirements and do not prove the behavior.

Use actual presentation properties of the action's rendered view/panel:
CanvasGroup opacity or RectTransform scale/geometry. The prepared UiClockSeconds
input and actual Shell.Refresh support deterministic progression. SHELL owns
adding/configuring any required runtime CanvasGroup and animating actual views;
the fixture must never add an expected animation, set expected output properties,
create a controller, or implement the transition. Binding/configuring visual
components is delegated behavior and should currently fail against the stubs.

Capture action-adjacent states and sample actual presentation at controlled
start, intermediate and completion times for BOTH open and Back/close. Observe
the actual Chat view while opening and the actual restored Lobby presentation
after Back. Require a meaningful visible-property change on the relevant panel,
intermediate progression and completed usable presentation. An already true
parameter, a running idle loop or mere activation is insufficient. The recording
UI stack is read-only and may destroy the outgoing Chat view; do not require
sampling a destroyed object. Pending human review still judges visual quality.

## L13-02: establish elapsed quiet time and change-driven acquisition

Set the prepared world.UiClockSeconds to a fixture-owned numeric clock BEFORE
binding. Its delegate only supplies time. Record actual UnreadChanged account
events and UnreadSnapshotRead calls. Those observers record only; they must not
update UI, invoke Refresh themselves or provide expected unread snapshots.

The test driver may tick real Shell.Refresh while advancing that clock across a
meaningful quiet interval (at least 30 seconds, with multiple intermediate ticks).
Settle initial binding/change first and distinguish explicit direct fixture reads
from UI observations. Require no new UI snapshot reads or unread-change events
during that quiet interval. Then deliver a real new message through Social and
require an affected-account change event, shared entry acquisition and actual
badge update; settle again and repeat quiet advancement. A fixed number of
UniTask.Yield calls without elapsed-time assertions is NOT this oracle.

SHELL must use this existing optional UI clock for its timer/update observations
(Unity unscaled time when unset), subscribe to the actual service change event,
cache a coherent active-account snapshot and avoid a separate quiet polling loop.
All delivery/read/counter behavior remains delegated to SOCIAL, all visual/update
behavior to SHELL. This guidance adds no fake outcomes or handwritten behavior.

Update the current clause map to the actual probes. All five named tests and
approved self-avatar, viewport, expansion and friend-action behavior remain.
