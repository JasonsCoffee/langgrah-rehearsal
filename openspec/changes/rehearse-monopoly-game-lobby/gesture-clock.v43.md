# Deterministic report gesture input and rendered-content boundaries

World.UiClockSeconds is a prepared optional Func<double> supplying a monotonic
client UI clock in seconds. Null uses the real Unity unscaled/realtime clock.
LobbyWorld.ReportHoldSeconds is the rehearsal's 0.5-second minimum report hold.
The fake server clock remains responsible for cooldown, expiry and records;
advancing it does not implicitly advance the UI clock.

SHELL records pointer-down time and recognizes the report long-press on pointer
release when the elapsed UI-clock duration meets that minimum. Short presses do
not open reporting. This defines deterministic release-based recognition for the
rehearsal. No event handler or report implementation is supplied by the Architect.

The message author can install a recording clock input, dispatch actual pointer
down to the rendered message, advance that input while held, then dispatch pointer
up and observe the real Report/confirmation/Confirm/Decline path. Do not write
popup state in the fixture. Pass the already available fixture/world/shell to an
owned helper instead of a fake lookup that returns null. Remove the invalid
untyped null ternary and all no-op clock helpers. The field and constant are now
actually declared; other authors' source remains read-only.

Literal text must be observed in delivered message content under the actual
history/scroll content, excluding Input and its descendants, status/marquee and
unrelated labels. Use parsed/rendered output; raw label.text need not equal the
original input. Correct invalid raw-string assertions rather than retaining a
constraint that contradicts allowed encodings.

Unsupported message-content images/emoji controls require actual content-role
and interactive-binding checks. Ordinary avatar/background/input graphics remain
valid. Reserved-slot checks inspect adjacent layout allocations, never internal
input-field graphics. All other valid delivery, Unicode, pending, cooldown,
friendship and feedback coverage remains required.
