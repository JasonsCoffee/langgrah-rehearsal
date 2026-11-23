# Verification and acceptance status

## Final backend closeout

Backend implementation is complete on isolated revision
`ac9416e998ee6ad022993350dc29aa0cc8236342`. The user's latest sequencing decision
defers lobby test-conflict corrections and further game execution. The backend
change neither approves nor completes the game.

- Full offline suite: **888 passed**, one existing TestResult collection warning,
  exit 0, 241.76 seconds. Final annotation-only cleanup: **22 focused checks
  passed**, exit 0. All 26 frozen host test/fixture hashes match.
- The unchanged graph compiled with `uv run --no-sync langgraph dev
  --allow-blocking --port 2029 --no-browser`; local assistant search listed
  `unity_coder`. The task-owned server was stopped. `src/`, original tests and
  both pinned overlay source files have no implementation diff from `b322e2c`.
- Authenticated direct DeepSeek and Codex model/effort preflights passed. Real
  direct Coder/selector receipts and GPT-6.1 Sol low SDK receipts qualified the
  routes. Future Coder stages and format repair share the direct low client.
- Packing format 2 passed all eight adjudicated paired reviews: **52.04% median
  Judge-input reduction**. These are compressible protocol fixtures, not a promise
  about production packets. Dollar savings remain unverified.
- Final clean-source canonical audit used actual archived compiler request
  `v70-step5-verify` at historical candidate
  `be19106e61f8c5ce78cdde53803573616b9334fb`. Both fresh low-Judge reviews identified
  the ECON-owned unsupported serializer API as an implementation defect. Actual
  input was 206,554 packed versus 208,008 canonical tokens; both receipts settled.
  This audit does not claim that the current candidate has that old compile error.
- Final current-candidate preview uses 93 admissible sources, zero owned author
  reports, and exact committed source bytes including CRLF. All completeness,
  integrity, dependency, filtering, identity, budget and savings checks passed.
  Its 2,232,918-byte canonical input becomes 2,231,554 bytes by free packing;
  no paid selector is used for this mandatory-heavy packet.
- `selected_backend(state, None)` returns `mixed` from the persisted activation.
  Stale Codex/OpenRouter overrides fail closed. The previous activation bytes
  remain in immutable activation history; original grants and receipts remain.

Aggregate accounting is **170,044,520 input / 6,520,897 output**, including the
same **27 uncertain reservations**. Limits remain **250,000,000 / 24,000,000 /
160 cycles / 2 added units**. The unchanged qualification sub-envelope used
3,066,732 input / 2,748 output of 10,000,000 / 512,000. Ordinary native reviews
remain fully charged to the aggregate ledger. Every pre-migration call entry,
cycle count and limit was preserved; all 199 frozen game files still match.

Final reports: `provider-migration.md`, `context-packets.md`, `pilot-report.md`,
`test-freeze.md` and `backend-final.json`. Trusted evidence is under
`S/context-optimization/`, `S/context-packets/`, `S/context-verdicts/` and the
original native run directory. The ledger is authoritative; the ended native
status snapshot predates later backend-only qualification calls.

## Final compliance and review

Both delta specs are implemented: explicit independent routes, local secrets,
durable actual/uncertain charging, preserved recovery, immutable exact sources,
extractive selection, bounded fallback/expansion, original Architect findings,
quality/cost reporting and unified optimized input/check results. Source filtering
and byte fidelity are enforced by code before dispatch and again at delivery.
No model's self-certification authorizes a packet. Unknown usage stops recovery.

Spec review preceded code-quality review. Final review additionally caught owned
test-author narratives being misclassified as evidence and native text loading
normalizing committed CRLF. New tests reproduced both before their guards were
implemented. The final source-only builder excludes those reports, retains all
actual code/tests/criteria/rules, and checks raw source against the committed
candidate. Earlier mixed-packet audit results remain historical evidence; the
clean compile audit is the final activation proof for source-filter version 2.

Seven real review observations are retained. The observer continues recording
the remaining first-ten window when the user resumes the lobby; its guard and
disagreement handling are already installed. No extra product execution was
manufactured to fill that window.

The lobby remains at cycle 70 **rework**, candidate
`625db77bf4e75060435947d955328a729f6f87dc`, contract
`bbbfcf9dc2b51f1ffb9d8a935a1fbb72ca148ada5c2a89f6b37752065f9315e7`.
Actual step10 selection: 129 executed, 39 passed, 90 failed, zero skipped;
nonbehavioral mixed failure evidence. All five independent reviews returned
contract findings. Confirmed frozen conflicts are documented separately; the
user has not authorized their correction. No `awaiting_human_review` or human
acceptance is claimed.

Review the isolated diff from `b322e2c` to `ac9416e` and the evidence above.
Normal future host invocation reads the persistent mixed-backend marker. Resume
the game only through its existing authorized contract/test workflow. No new
dependency, framework-runtime fix, handwritten game implementation, mainline
commit, push, merge, archive or human approval is part of this delivery.

## Earlier verification notes — historical snapshots

This is an Architect self-review of host wiring, not an independent approval of
the game. Implementation checkpoints are `cf09728` and `a210e1d` on the existing
isolated backend branch. Shared runtime, settled design, original tests, all 199
frozen lobby files and both pinned overlay sources remain unchanged.

## Commands and observed results

- Isolated checkout: `uv run --no-sync pytest -q --tb=short`, with the existing
  virtualenv, UTF-8 and `src` import path: final exit 0, **860 passed**, one existing
  TestResult collection warning, 270.31 seconds. Prior pre-audit run: 855 passed
  in 254.49 seconds. Frozen host-test hashes remained unchanged.
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
- Full physical 81,134-file baseline/import scan passed before pilot and during
  native recovery. Bridge identity/capability preflight also passed. The trusted
  recovery authorization retains all 27 unknown calls. Public recovery reached
  fresh `v70-step9-verify` on the unchanged candidate with 129 selected tests.
  Verification and actual new-policy game-effect receipts remain pending.

The fresh step9 operation subsequently completed compile, then stopped before
test submission with `No exact-project Bridge with FrameworkVerify tooling`.
Evidence SHA256 is `a9d96d1f00aa706af2d4a7e79301c46a3730120dd084cc3fccaed09d2cbfffef`;
compile callback SHA256 is `97d1db9141c7c776a02feece22fb7c798faed5a002ccfe7ff00f3d2e84d76519`.
The exact tests ticket has neither request nor result. Independent read-only
health, project-info, capability and native discovery probes then succeeded.
This establishes recovered discovery, not a proven underlying timing cause.
Host-only checkpoint `fe8d3a4` adds a one-boundary public native recovery; seven
new frozen tests plus existing discovery/recovery tests passed **28 cases**.
Those seven first failed on module absence. One fresh retry is running; shared
transport runtime, pinned overlay, source and all old evidence are unchanged.

## Spec compliance

| Requirement group | Evidence and status |
| --- | --- |
| Direct Coder, explicit low independent Judge | Mixed profile/client and genuine paid role receipts pass; future native effect activation pending |
| Local keys and constrained destination | Ignored local configuration, TLS/redirect refusal and frozen transport tests pass |
| Complete accounting and unchanged ceilings | Native shared ledger, settled pilot and exact old-call preservation pass; 27 unknown reservations retained |
| Same-run recovery | Exact-boundary, historical receipt, candidate, freeze and stale-effect tests pass; public native recovery completed and fresh verification started |
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
