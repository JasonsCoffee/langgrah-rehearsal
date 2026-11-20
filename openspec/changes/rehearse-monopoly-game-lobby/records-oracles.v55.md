# Records: populated, independent client/fake-backend oracles

The actual cycle-54 dossier is mandatory. All 24 mapped methods remain required.
Write actual assertions against runtime services, bound controls and rendered
instances; expected failures against stubs are legitimate TDD. No fake adapters
may return expected business outcomes or render expected rows.

## Prepared data clarifications

- Configuration.RankingDayHours=24 and RankingWeekDays=7 are the single shared
  configurable rolling-window source. The user chose rolling windows, not fixed
  epochs or local-midnight resets. B-only midnight/timezone clauses do not switch
  this rehearsal to B; straddling Shanghai midnight must not reset a rolling A
  window. Snapshot.TimeUtc is one fake-server-clock timestamp for both lists.
- LobbyIncome.Round carries journal round metadata; match/account identity comes
  from its enclosing record. Preserve source, amount, timestamp and round through
  actual persistence/reconstruction and shared ranking/history/detail consumption.
- LobbyMatchRecord.PropertyValue and Debt are explicit fake-upstream inputs for
  exclusion/debt stimuli. BankruptcyOrder carries upstream ordering evidence;
  Rank remains the fake final-rank input, never recomputed by the client.
- Publish is the fake records-backend intake. It consumes actual supplied journal
  and cash/fee/abandonment inputs and derives/validates the canonical record.
  Do not prefill the expected Profit/TotalIncome/TotalExpenses and merely assert
  their pass-through. Completed profit is EndingCash-EntryFee, property excluded,
  with pool income already in EndingCash. Abandoned profit is -EntryFee and
  expenses=eligible income+EntryFee (approved option B), including debt cases.
  Normalized abandoned ending cash is zero. Derived totals must reconcile.
  Rankings aggregate eligible positive rent/lottery/event/pool income, excluding
  revival transfers and every expense; preserve the same underlying journal.
- RulesTextKey points to the new lobby.rules entry in the game-owned rehearsal
  LocalizedText table. This is separate from VIP benefit keys. Rules() consumes
  the configured key. Tests may replace that actual localized input with long
  rich text, then inspect the real popup. Default prototype copy is prepared data.

## Required observations, grouped for the author

| Scope | Effective probes |
|---|---|
| L5-01,06,07 | Distinct retained scroll positions per real tab; populated inside/exact/outside rolling cutoffs, both shared parameters varied independently, explicit fake-clock expected snapshot timestamp, identical snapshots for accounts at the same time, correct rolling copy. No self-comparisons or empty snapshots. |
| L5-02,03,05 | Distinct eligible categories, excluded revival/expense inputs and different cash expenses; multiple matches with round/source/time metadata, actual persistence restart, shared detail provenance; equal totals with income/entry/publication orders deliberately different. |
| L5-04,08,09,10 | Visible formatted amounts, medals, long-name layout; at least 105 independently ranked accounts, actual ten-row pages through rank 100 and exhausted loading; ten ranked rows PLUS a separately visible styled pinned self row, including nonzero income below rank 100 and persistence across pages. Row9 alone is not the pinned row. |
| L5-11, L6-01,04 | Real bound detail expansion/collapse, exact individual journal entries, single-expanded-row behavior and stable order; visible history fields and real lazy loading. Returned DTO values alone do not establish UI behavior. |
| L6-02,03,05,06 | Cash/fee/journal inputs with independent expected derived results, explicit property and debt stimuli, approved B, visible abandoned rank and exclusion wording, final supplied ranks including bankruptcy order; all-player pool/rake reconciliation. Do not compare one player's profit to a global rake equation. |
| L8-01,02,03 | Same Settings screen from Lobby and real fake-match context, context-owned exit visibility/action; second account; both audio directions and effects, save then genuinely reconstruct session without manually seeding expected preferences; device defaults and restored overrides, actual framework quality tiers and two-state layout. |
| L8-04,05,06 | Simulated support/back; real localized rich-text Rules popup, actual overflow/scroll and bounded geometry, no empty tabs; plain-text About/version popup with no QR/link controls and usable geometry. Negative checks use actual roles/references. |
| Journey_RECORDS | Actual paging, nondefault tab/row selection/scroll, expansion, settings effects and exact caller/page/selection/scroll restoration. A default week tab is not restoration evidence. |

All UI actions use the actual bound controls and independently verify active
state, opacity, dimensions and clipping/usability. Scope text to its real content.
Keep one entered street fixture at a time and dispose before reconstruction.
Use real recording interfaces from the supplied harness; do not invent APIs.

For a simple coherent pool stimulus, 24 entry fees of 100 form a 2400 pool;
after 5% rake, independently supplied ending-cash values must sum to 2280.
Assert each actual derived profit=cash-100 and their sum=-120. This is fixture
input/expected arithmetic, never a prefilled set of output profits. Other coherent
distributions are valid. Income, expense and profit fixtures must reconcile.

Use test-first strict hash-bound output, finite helpers and truthful current maps.
Preserve the source meanings and pending qualitative human checks. No compilation,
execution or human acceptance is implied by source review.
