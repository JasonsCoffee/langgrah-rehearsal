# Token ceiling repair — 2026-11-19

The follow-up request to fix token ceilings authorizes the narrow model-boundary
and worker-allocation edits below. Lobby implementation, runtime recovery,
governor transitions, overlay checks and previous runs remain outside this repair.
This is a code-only review; it is not a functional lobby review candidate.

## Failure and correction

Two framework validators independently rejected any allowance above 32,768.
The worker default was 4,096 for every stage. The lobby host additionally selected
32,768 for test authors and SHELL implementation, 24,000 for other implementation,
8,000 for refactoring and test review, and 4,000 for defect judgment. Increasing
the aggregate run budget could not increase those per-call allocations.

`StageTokenBudgets` now configures all five paid stages. The checked-in
`token-policy.json` explicitly selects:

| Stage | Output reservation |
|---|---:|
| Test authoring | 65,536 |
| Green implementation | 65,536 |
| Refactoring | 65,536 |
| Independent test review | 32,768 |
| Defect judgment | 32,768 |

These allocations are configurable, not maximum framework capabilities.
Both model-boundary validators now use the same positive-integer and optional
per-role model-cap validation. Local AI configuration may supply
`max_output_tokens` using the selected endpoint's documented cap. No capability
value was guessed or added to the credential-bearing configuration; provider
capability enforcement remains authoritative when that optional field is absent.
No model, routing, reasoning or temperature configuration was changed.

The context assembly guard remains 600,000 UTF-8 bytes, explicitly configured in
the same policy. Final prompts still receive native conservative input reservation.
Every stage reserves its full allocation against the existing persistent ledger
before dispatch. No request is silently clamped to fit a model or remaining budget.
Reported usage, uncertain reservations, call identities and replay checks remain
unchanged. The historical one-time recovery operations retain their recorded
allowances; these were not invoked or rewritten under existing paid-call IDs.

## Frozen verification

Tests were written and exercised before the corresponding implementation edits:

- `tests/test_token_limits.py`: 19 failed, 5 passed before implementation.
  Frozen SHA-256 `41d7111edab0a4a911af6710538d95fc8ebc087e1f10b6530babaa29ed800349`.
- `test_token_policy.py`: 7 failed before host wiring implementation.
  Frozen SHA-256 `b271a5180b4d04aa3e9c977eeba577de6758990fceb1877b27908dd5532629b8`.

The focused model/worker suite passes 46 tests; the host composition passes all
7 tests. Coverage includes allocations above the old ceiling, every paid stage,
invalid values, configured model caps before reservation, persistent input/output
ceilings, uncertain-call reconstruction, replay without a second charge, and
changed-allocation identity rejection. All model responses are offline fakes.

Full-suite verification: `uv run pytest -q` passed **503 tests** in 243.44 seconds.
One existing collection warning concerns the `TestResult` dataclass imported by
`tests/test_human_review.py`. The seven separate host composition tests also pass.
Both frozen test hashes and all four preservation identities below match after
verification. `git diff --check` passes.

The development graph compiled and was listed as `unity_coder` using
`uv run langgraph dev --allow-blocking --host 127.0.0.1 --port 2027 --no-browser`.
The installed server first failed decoding its bundled OpenAPI file under Windows
GBK; process-local `PYTHONUTF8=1` resolved startup without dependency changes.
The listing was confirmed through `/assistants/search`, then the server stopped.
No graph execution, paid model request or Unity execution occurred.

## Preserved run and review limits

Run budget remains **3,000,000 input / 900,000 output**, three cycles, two added
units. Existing usage remains **918,325 input / 300,946 output**. The run remains
`abandon / budget` at cycle three with preparation candidate
`c5143932bf382787c5504793a44871b8a2a48c3a`; it has not reached
`awaiting_human_review`. Token ceiling repair does not reopen that terminal state
or complete the missing test preparation and delegated lobby implementation.

The following SHA-256 identities were captured before the repair and checked
again afterwards:

| File | SHA-256 |
|---|---|
| Native budget ledger | `6a92f87b6d983b85f4621a9765df91907f4fdd23cf8ab6c64bce3c459b350751` |
| Native result | `69eec72db3154cf5eede246bc106f90482e7464bcaf3f79a0ccfe68886100b84` |
| trusted_overlay.py | `851246aa66bc5cb68a18ed97d6df0e29f0c63ef5071e94bf3329e45c89b5479f` |
| overlay_host.py | `53301fcbc46abc2c7d316b9fd82af64e8fdc19bfbe71a23d8a0f19390ac2c190` |

Review the three core Python diffs, example configuration and allocation guidance
in `docs/loop-control.md`, then the host composition and `token-policy.json`.
Re-run `uv run pytest -q` and the host's `test_token_policy.py` for offline review.
Provider-specific caps and real response completeness were not live-tested.
There is no human acceptance record, commit, push or merge for this repair.

The framework-architect guidance was sufficient on preserving paid-call identity,
budgets, frozen tests, and reporting actual outcomes. It supplies no automatic
stage-allocation policy or abandoned-run recovery. This repair supplies explicit
stage wiring; recovery remains a separate capability rather than an invented
transition or budget reset.
