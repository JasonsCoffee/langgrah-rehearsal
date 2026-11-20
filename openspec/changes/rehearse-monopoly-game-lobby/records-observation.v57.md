# Records: typed cells, page boundary and remaining exact fixtures

The actual cycle-56 dossier remains mandatory. All 24 named tests and every
effective prior assertion remain. These additions are nonfunctional declarations;
the configured Coder implements every backend/UI behavior and test assertion.

## Actual dynamic binding protocol

For populated record/ranking rows, LobbyControlBinding now declares references to
the actual RankLabel, NameLabel, AmountLabel, ModeLabel, TierLabel, TimeLabel,
IncomeLabel, ExpensesLabel and MedalGraphic. SHELL binds these to the actual
visible components it renders; no unrendered diagnostic labels are allowed.
Fields irrelevant to a row kind may be null. Existing Label/Button remain.

| RowKind | RowEntityId | Required actual references |
|---|---|---|
| ranked | synthetic account ID | rank, name, amount; actual medal graphic for ranks 1–3 |
| pinned-self | active synthetic account ID | rank, name, amount, distinct fixed presentation |
| history | match ID for active account | rank, mode, tier, time, profit amount; visible income/expense fields while expanded |

There are TEN ranked rows plus a SEPARATE pinned-self binding, including when self
also appears among those ten. Never reserve Row9 for self. Inspect active state,
ancestor opacity, effective viewport/screen geometry and clipping; local anchored
position alone is insufficient. Assert rank and amount through their own actual
rendered fields, so 100+ rank cannot satisfy a 100/0 amount assertion. Names and
IDs must match exactly; P1 is not P10/P100. Require real medal graphics for all
three podium ranks, not text colors. Retain formatted amounts and actual visible
long-name truncation observations. Fixtures never populate these row outputs.

LobbyRehearsalViewBase also declares actual Overlay, OverlayText, OverlayScroll
and LoadingIndicator references. SHELL sets them to the real runtime overlay and
loading presentation when present. Rules/About must be real bounded overlays;
Rules uses its actual scroll content and complete localized rich text. About
content is plain text, with no QR Image/RawImage or link controls in its content
region. Legitimate outer background/close controls are separate roles. A loading
indicator may be absent for the synchronous fake service; any shown indicator is
bound and must stop at completion. Do not manufacture outcomes in test adapters.

## Fake ranking-page boundary

ILobbyRecordsSettings/LobbyRecordsSettings declare RankingPage(accountId, week,
page, pageSize, snapshotUtc), returning LobbyRankingPage (TimeUtc, Page, TotalCount,
HasMore, Rows). This consumes the actual captured shared ranking snapshot, capped
at 100; page size ten gives pages 0–9. An out-of-range page returns no rows and
HasMore=false. World.RankingPageRequested observes actual request arguments and
returns nothing. SHELL uses this boundary for actual Next/scroll-driven loading,
retaining the captured timestamp. A direct out-of-range backend probe is distinct
from UI observation windows. Test all populated page membership/ranks, final
HasMore/indicator state and no additional UI request after termination. Never use
History(acc-A, ...) as evidence for ranking pagination.

## Exact remaining fixes

- Coherent cash fixtures: cash 300, fee 100, eligible income 300 implies profit
  200 and expense 100; cash 400, fee 100, income 500 implies profit 300/expense
  200. Do not prefill derived outputs. For two published matches, assert the
  actual aggregate sum across both, not the first match alone. Debt must differ
  from income (for example debt 77 vs income 900) so fee+debt cannot pass option B.
- Capture original day/week configuration before mutation and restore those
  actual captured values before checking default 24-hour/7-day copy. During a
  changed configuration, require matching changed copy and populated results.
  This rehearsal uses inclusive [snapshot-window,snapshot] bounds. Straddle
  Shanghai midnight without resetting rolling windows; B-only fixed-midnight
  rules do not override the approved A selection.
- Use the exact visible rank-column value for final supplied bankruptcy rank
  and 已放弃. Expanded details show BOTH income and expense totals and supported
  expense categories; one click expands, the next collapses, order stays fixed.
- Isolate per-account observation windows in a SHARED preference store. Capture
  lengths or clear logs before B, rather than applying B-only predicates to A's
  old writes. Test music-off/effects-on, effects-off/music-on and both on again.
  Reconstruct a fresh world/coordinator from actual saved data and require fresh
  preference reads; do not reuse changed world state or manually seed outputs.
- ILobbyUiPort ALREADY exposes DeviceQualityTier, LowestQualityTier and
  HighestQualityTier. Use these real declared inputs, both states and restored
  overrides. A binding adapter may apply the actual requested framework quality
  tier/effects when production requests it, recording that request; the fixture
  may not independently apply an expected state after the click. Check the real
  configured tier/effect values, not just an accumulated call list.
- Rules must exercise a different configured RulesTextKey as well as long
  translated content. No VIP-key substitution. About checks actual content roles
  under the real overlay, not English-name blacklists.
- Remove synchronous GetResult from entry/open/shutdown paths. Use async test
  methods, an async fixture factory and awaited cleanup in finally. One entered
  street at a time. Dispatch actual pointer events only after usability checks,
  then wait for the actual command outcome with a bounded runner-compatible
  async wait. Intentionally disabled Next gets a real ignored pointer attempt;
  invoking its onClick event directly bypasses the behavior under test.
- Journey_RECORDS must establish nondefault page/selection/scroll and expansion
  before testing restoration, with expected amounts from THAT selected page.

Correct all current clause maps; comments and configured input values are not
evidence of runtime consumption. Do not add business behavior to fixtures or
claim execution/human acceptance from this source review.
