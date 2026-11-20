# Repair the helper owner before its consumers

The actual cycle-40 dossier identifies a compile defect in ChatFocusInput, owned
by TEST-CHAT-MSG, that blocks the shared Social fixture. Social cannot edit that
file. The next contract schedules the message author immediately after HARNESS,
and Social depends on that repair. The message author may read the already
prepared Social fixture helpers without waiting for another Social authoring
pass. No helper implementation is supplied by the Architect.

The message author must fix its actual TMP input event signature, then cover its
four mapped sending/permissions/plain-text/cooldown/reporting methods. Use the
declared delivery gate to observe the real Send control during the actual call
and inject a failure without committing a message. Observe the click's own
delivery and preserve drafts on rejection. Advance fake time between successful
world-message fixture sends. Test both world and private Unicode limits.

Long-press/report/confirmation/cancellation and configured cooldown changes need
real bound stimuli and observed results. Literal rendering is a presentation
requirement; do not impose an unstated persistence escaping scheme. The user's
visible own-avatar override still applies.

Read chat-authoring.v39.md. Assertions against the real nonfunctional stubs are
expected baseline Red. Test helpers must not manufacture business outcomes.
Shared Social source remains read-only to the message author; other source
authors revalidate normally after the actual helper owner has repaired it.
