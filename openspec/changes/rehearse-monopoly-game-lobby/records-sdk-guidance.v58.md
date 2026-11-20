# Records: actual SDK and complete prompt context

Cycle 58 supplies the complete late guidance and the actual SDK source export.
Earlier contracts named guides that the trusted prompt curator omitted. This was
an Architect host-wiring defect, not permission to waive any source requirement.
All seven actual cycle-57 findings and all 24 enabled tests remain mandatory.

## Prepared dependency slots

LobbyShellBindings declares instance-owned DeviceRatingService,
QualityMatchingService and QualityModifyService using the real jj.Core.Runtime
interfaces; DeviceRatingConfiguration and QualityMatchingConfiguration are
ScriptableObject inputs. These declarations contain no outcomes. SHELL must bind
and consume the actual framework services in production. Tests may inject input
providers or tracing proxies with proper lifecycle, but cannot fabricate quality
effects or independently set expected render state after clicking.

ILobbyUiPort already declares device, lowest and highest tier inputs. Those are
presentation inputs, not proof that SDK matching or modification occurred. Assert
the actual device-rating/matching calls and the actual requested low/high tier.
For effects, exercise the real framework modifying boundary and inspect each
required effect independently: shadow state, resolution/render scale and particle
configuration. A record-only ApplyQuality or a single combined string inequality
is insufficient. Save and restore every touched global/engine state in finally.
Do not invent enum values or service signatures: use framework-quality-context.

QualityDetail is a struct containing name and Dictionary<string,int> detailMap.
QualityMatchingConfigObject has deviceKey and configList with nested ConfigList /
ConfigElement records. The actual modifier must be started before use; it creates
its internal handler in OnStart. Its external IQualityHandler is invoked by the
real modifier with the supplied detail. Custom game particle handling belongs to
production SHELL, not fixture code. Internal handler uses the framework Injector
and IUserDefault; own/release any temporary injected services and avoid disturbing
the host's active services. The exported existing SDK tests illustrate lifecycle
only; do not run them or copy their missing guards.

The test assembly references public Bifrost interfaces but does not directly
reference the concrete Core runtime assembly. Use existing loaded-service / public
interface seams, or carefully resolved loaded types for a real SDK integration
fixture. Do not edit existing asmdefs, SDK, project settings or framework runtime.
An unavailable engine capability must be reported with evidence, never silently
replaced by an assertion against a test-written effect implementation.

## Remaining exact source-review corrections

- Await the specific action outcome: screen/route identity, overlay visibility
  and content, row expansion fields, page identity, or actual quality effect.
  Include bounded runner-compatible waiting and awaited shutdown. Generic any-
  fingerprint changes can pass too early or miss legitimate unchanged refreshes.
- L5-02 independently supply deductions and a nonzero entry fee; exclude negative
  rent/event/lottery entries from income and bankruptcy liquidation from expenses.
  Keep cash, income and expense fixtures coherent and distinguish debt from income.
- L6-03 requires the actual visible profit cell to include the negative fee and
  abandonment annotation, separately from the rank cell's 已放弃 and backend data.
- L5-07 must straddle Asia/Shanghai midnight with populated timestamps and actual
  rolling results; no calendar conversion-only assertion or unauthorized deferral.
- L5-11 correlate each displayed detail with its persisted journal identity/source
  and signed amount. A Status string containing two numbers proves neither.
- L8-06 derive the displayed version from the actual package/build version input,
  not the fixed lobby-test sentinel. Inspect the actual About content region and
  require plain text with no QR-bearing Image/RawImage or link controls, allowing
  the legitimate background/close controls by explicit roles, not name blacklist.

Read records-observation.v57.md and records-oracles.v55.md verbatim. Do not
overwrite or weaken other accepted assertions. Update clause maps truthfully.
Source review remains separate from compilation, execution and human acceptance.
