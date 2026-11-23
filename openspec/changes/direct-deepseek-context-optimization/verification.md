# Verification and acceptance status

This is an Architect self-review of host wiring, not an independent approval of
the game. Implementation checkpoints are `cf09728` and `a210e1d` on the existing
isolated backend branch. Shared runtime, settled design, original tests, all 199
frozen lobby files and both pinned overlay sources remain unchanged.

## Commands and observed results

- Isolated checkout: `uv run --no-sync pytest -q --tb=short`, with the existing
  virtualenv, UTF-8 and `src` import path: exit 0, **855 passed**, one existing
  TestResult collection warning, 254.49 seconds. This run predates the five
  appended rollout tests; do not describe it as an 860-case execution.
- Appended rollout tests plus existing optimizer integration and mixed feedback:
  focused pytest exit 0, **10 passed**, 0.24 seconds.
- Earlier full run: 854 passed. Graph validation used
  `uv run --no-sync langgraph dev --allow-blocking --port 2029 --no-browser`;
  the graph compiled and local assistant search listed `unity_coder`. Only the
  task-owned development-server session was stopped.
- `git diff --check`: exit 0. Frozen host inventory: 17 files, zero changed hashes.
  Main planning `pnpm exec openspec validate direct-deepseek-context-optimization
  --strict` passed before the added evidence reports; final validation follows.
- Authenticated read-only provider/model preflights passed without secret output.
  Paid pilot exited 0 with qualified=true. See `pilot-report.md` for actual
  comparison correctness, overhead, identities and limitations.
- Full physical 81,134-file baseline/import scan passed before pilot. Native
  activation repeats identity/capability and baseline checks; this pending scan
  must not be represented as a completed activation.

## Spec compliance

| Requirement group | Evidence and status |
| --- | --- |
| Direct Coder, explicit low independent Judge | Mixed profile/client and genuine paid role receipts pass; future native effect activation pending |
| Local keys and constrained destination | Ignored local configuration, TLS/redirect refusal and frozen transport tests pass |
| Complete accounting and unchanged ceilings | Native shared ledger, settled pilot and exact old-call preservation pass; 27 unknown reservations retained |
| Same-run recovery | Exact-boundary, historical receipt, candidate, freeze and stale-effect tests pass; public native activation requested, not yet completed |
| Canonical evidence identity / exact source | Manifest, stale hash, literal bytes, full live test/helper integration and mandatory closure tests pass |
| No worker self-assessment / secret input | Source-only builder and forbidden-source tests pass; config and worker reasons are excluded |
| Extractive selection and deterministic packing | Twelve adversarial fixture cases and exact UTF-8 span/injection/dedup tests pass |
| Bounded expansion and fallback | Strict native schemas, exact source IDs, one expansion and canonical fallback tests pass; uncertain calls stop |
| Shared selector/audit budget and no replay | Durable selection intent/cache, retained unknown usage and persistent envelope tests pass |
| Exact Architect findings | Classification/explanation and unresolved-reference tests pass; original verdicts remain authoritative |
| Measured quality and net benefit | Four paired protocol classes pass expected findings and reduction gates; dollar saving is unproven |
| Rollback / policy-specific reuse | Medium remains historical, low grant and cumulative role bound tests pass; disabled classes use deterministic context |
| Input plus check results on every path | Persisted optimizer result, checks, fallback/blocked and forged/self-certified report tests pass |
| Live observation / canonical audit | Host helper and frozen tests pass; actual first-ten-review observation and paid canonical audit pending |
| Lobby acceptance | Unmet: real selected tests and candidate-bound visual review still required; no human acceptance is claimed |

## Code-quality review

Review followed spec compliance, then destination/secret boundaries, historical
policy handling, exact bytes, call identity, accounting and ownership. Findings
resolved in host code: JSON escaping changed literal source representation;
effort-policy changes could refill the old Judge claim bound; expanded reviews
needed their actual final SDK receipt; mixed runtime evidence needed a distinct
packet class; active rollout needed persistent canonical-audit and disagreement
guards. Frozen tests were not changed to fit these repairs.

Conservative limits remain explicit: full supplied C# is retained instead of a
claimed precise semantic closure; raw sources cannot be replaced by hash-only
references. Optional context can still influence attention, so pilot agreement
does not prove general equivalence. Estimates use conservative UTF-8 bounds;
provider usage is authoritative. The expensive original overlay scans are kept.
No new dependency, shared runtime change, hand-authored game repair or automatic
human approval was introduced.
