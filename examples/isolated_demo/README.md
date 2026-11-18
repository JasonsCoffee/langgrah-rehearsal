# Isolated live demonstration

This opt-in diagnostic runs two deterministic coding callbacks in parallel and
verifies their integrated output sequentially in an already-open dedicated
Unity host. It exercises real worktrees, mediated ownership, frozen tests,
shared failure attribution and callback-based EditMode evidence. It does not
exercise model generation, the independent judge, the exported LangGraph, or
human acceptance. Existing game tests are outside this diagnostic's selection.

Set machine-local `UNITY_HOST`, `DEMO_ROOT` and `UNITY_BRIDGE_PORT` selectors.
The host must have the game mount at `Assets/JJGame/monopoly`, the packaged
verifier installed, and resolved packages. `DEMO_ROOT` must be external to the
host and start empty. The only game overlay is
`Editor/Script/FrameworkDemo`. Never select an interactive development project.

Run from the framework repository:

```powershell
uv run python examples/isolated_demo/run.py prepare
uv run python examples/isolated_demo/run.py demonstrate
```

Preparation creates a disposable module repository, stubs and five tests. It
requires compilation followed by five actual test failures before freezing
hashes and committing the baseline. Implementation then runs both units,
integrates A first to demonstrate the shared failure, integrates B, and requires
all five tests to pass twice. The second pass confirms the explicit no-change
Refactor decision. All frozen inputs must retain identical bytes in both coding
worktrees, integration and the verifier host.

Evidence is written under `DEMO_ROOT`; `summary.json` is emitted only after every
assertion succeeds. Read callback counts and provenance, not merely Bridge task
completion. Failed attempts retain their worktrees. Use a fresh `DEMO_ATTEMPT`
identifier to rerun after reconciling the editor; requests are never blindly
resubmitted. No repository is pushed and no mainline is changed.

The fixture disables Git's automatic newline conversion before its first
commit. Worktree checkout also overrides machine newline defaults. Hash checks
remain authoritative; explicit repository filters or attributes may still need
reconciliation before frozen-byte acceptance.

With `ai.local.toml` configured, run
`uv run python examples/isolated_demo/real_models.py` using a fresh DEMO_ATTEMPT.
This reuses the frozen fixture, observes fresh Red, asks the independent judge to
classify each unit's defects from evidence, runs real coder calls in parallel,
and requires sequential Green and Refactor confirmation. Model outputs are parsed
as owned-file JSON; they receive no shell or editor access. Paid calls use the
durable budget ledger. The harness stops and preserves evidence on an unexpected
failure; it is not the production retry/resume graph. It never grants human approval.
