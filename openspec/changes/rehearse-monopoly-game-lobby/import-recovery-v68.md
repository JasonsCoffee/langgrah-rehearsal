# Cycle-68 import reconciliation

The five-unit candidate `d6304a1b906bb340eeedccb01c57dc1393d02fe3` reached
`v68-step7-verify`, then import readiness timed out before a dedicated compile or
test request was submitted. A later exact-project Bridge probe reported protocol
1, compile/tests capability, ready=true and no active ticket.

Full import checks then correctly rejected a source change: the host's
`Runtime/Script/Monopoly.cs` had one additional **64-byte** GeneratedBreak /
Context.Break block at the start of OnDestroy. The committed implementation had
moved its existing generated block into DestroyOrdinaryService. Original entry
SHA256 `35a9f72e602f60d511d9b39da9f84d4104040298d83827028151692473ba2f00`;
observed SHA256
`6ce58408a8135559d008b9a70ccbacf296ebf4a24b572bfbaff278c9a1fcd98b`.

The trusted operator archived the observed bytes outside Unity imports, checked
the complete baseline/candidate inventory and identified only this exact source
insertion. The pending effect was reconciled through DurableEffects with an
actual ownership/import-drift VerificationResult, not fabricated compilation or
test evidence. All 195 frozen files and all accounting remained unchanged.

Judge (GPT-6.1 Sol, medium) actually classified this as **implementation** within
SHELL ownership, requiring preservation of generated lifecycle code and drift
checks. Native repair is now delegated through the same run. Auto-import logs
also contain three owned JJCK0011 cancellation-catching errors; those messages
are supplied as explicitly labelled import diagnostics, not a dedicated compile
receipt.

The one-time candidate-advance wiring requires a clean admitted descendant, a
generated lifecycle block inside OnDestroy, the complete retained test inventory,
and an exact full old-host snapshot differing only by the already archived
insertion. It writes only the admitted candidate inside existing allowed mounts,
preserves old history, uses the overlay's incomplete-install flag, and checks the
full baseline/candidate bytes afterward. Normal refresh/import and verification
follow. Unrelated drift or an interrupted write fails closed. It does not adopt
arbitrary C# generation, exempt sources from checking or modify the trusted
overlay implementation.

Six pending-effect checks froze at SHA256
`aa4323cd8baa41f9f6865239b9aefe157981fa3c7ba5fecf942f7b091651ea3d`;
six generated-drift checks froze at
`137248c97f119d20e6f1b5596848011641948510374b8c133d612bd5593b21cf`.
Both were observed Red before implementation. Full offline regression: **742
passed**, one existing warning, 285.33 seconds. Four additional materialization
integration cases passed before real candidate advance; their SHA256 is
`2e239892636669269e0c70d2e902c46f652c208150c849847f563a120d07d305`.
Those checks cover baseline preservation, rejection of unrelated drift, required
lifecycle repair and fail-closed partial installation.

The Architect/apply skills sufficiently require preserving generated boundaries,
exact effect reconciliation and full candidate-bound verification. They do not
supply this host-specific recovery for an existing owned C# file changed during
import. That wiring was supplied here. Framework coordinator runtime and the
two pinned trusted-overlay source files remain unchanged. No game implementation
was handwritten, no Judge was bypassed, and no human acceptance was recorded.

The `LOBBY_RECONCILE_IMPORT_V68` flag has now resolved the pending effect and is
consumed. Do not replay it on another reconnect. This is not awaiting_human_review.
