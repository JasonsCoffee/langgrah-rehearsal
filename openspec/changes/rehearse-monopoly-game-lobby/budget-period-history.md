# Token accounting period after backend migration

On 2026-11-23 the user explicitly authorized a fresh token allowance after the
backend migration: 20,000,000 input and 2,000,000 output tokens. The user then
clarified that contract cycles must retain their existing numbering, with a
cumulative ceiling of 120. This supersedes the earlier 250M / 24M / 160 policy
for future dispatch; historical authorizations and receipts remain unchanged.

Current token-period usage starts at zero. Native contract cycle remains 70 of
120, leaving 50 further cycles. There is no native cycle reset or renumbering.
The same run, candidate, contract, models, trusted overlay and frozen tests remain.
Game execution remains deferred; this amendment does not approve test corrections
or human acceptance.

## Historical accounting retained

| Accounting at the boundary | Input tokens | Output tokens |
|---|---:|---:|
| Settled usage | 140,584,433 | 5,275,713 |
| Uncertain reservations | 29,460,087 | 1,245,184 |
| Total accounted | 170,044,520 | 6,520,897 |
| Previous cumulative ceiling | 250,000,000 | 24,000,000 |

All 1,142 call entries and 70 cycle entries survive unchanged, including the 27
uncertain calls. Their complete prior ledger, policy, backend marker and result
are saved under the trusted state selector
`budget-periods/post-backend-20261123/`. Hashes and verification results are in
`budget-period-20261123.json` beside this document. Older uncertain calls remain
fully reserved; reconciling one requires an explicit amendment so it cannot
silently increase this period's allowance.

## Enforcement and observation

The unchanged native ledger enforces cumulative ceilings of 190,044,520 input,
8,520,897 output and contract version 120. Subtracting the preserved token
baseline gives exactly the new 20M / 2M allowance. No historical receipt is
deleted or rewritten. The host separately verifies this user-authorized allowance
without changing historical model grants, profile identities or pilot receipts.

The isolated backend's `lobby_budget_period.py` reports current token-period
usage and native contract cycle by default. Supply `LOBBY_RUN_ROOT` and use the
same isolated backend Python source environment as the production host. Its
explicit `--apply` path refuses an existing period; observing status cannot reset
the allowance. The implementation is host wiring, not a framework runtime change.

Verification: 20 offline checks passed, including native reservation/cycle-limit
enforcement and historical-drift rejection. All 26 existing frozen host fixtures
and all 199 frozen game files matched their original hashes. No model call,
Unity execution or game-source modification was performed for this amendment.
