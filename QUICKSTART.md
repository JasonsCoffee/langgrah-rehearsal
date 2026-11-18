# Quick-start menu

Codex + OpenSpec plans the work. LangGraph runs isolated coding units through
Red–Green–Refactor, with sequential verification and human review. Unity/C# is
the first adapter. Run commands below from the framework repository root.

| I want to… | Start here |
|---|---|
| Install and check the framework | [1. Offline setup](#1-offline-setup) |
| Configure the coder and judge | [2. Model configuration](#2-model-configuration) |
| Try the isolated Unity demonstration | [3. Unity demonstration](#3-unity-demonstration) |
| Execute a feature from OpenSpec | [4. Feature workflow](#4-feature-workflow) |
| Check progress or handle a stopped run | [5. Progress and review](#5-progress-and-review) |
| Review implementation status and limits | [Final verification](openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/verification.md) |

## 1. Offline setup

Prerequisites: Git and uv; Python 3.12 is pinned by the repository. For OpenSpec,
also install Node.js 22.12+ and pnpm, then use the repository's pinned CLI.
Unity and model credentials are unnecessary for framework tests.

```powershell
uv sync --frozen
pnpm install --frozen-lockfile
$env:PYTHONUTF8 = '1'
uv run pytest -q
```

The last full suite passed 478 tests, with one existing collection warning;
subsequent focused checks covered the added Architect-observation regression.
To inspect the graph locally:

```powershell
uv run langgraph dev --allow-blocking --no-browser --port 2025
```

Keep that terminal open. In a second terminal, list the graph:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:2025/assistants/search -ContentType application/json -Body '{}'
```

Expect `unity_coder`. Stop the server with Ctrl-C when finished. Starting this
server checks graph availability; it does not provision a target or start coding.

## 2. Model configuration

Create the ignored local configuration only if it does not already exist:

```powershell
if (!(Test-Path ai.local.toml)) { Copy-Item ai.example.toml ai.local.toml }
```

Fill in both `[coder]` and `[judge]` sections:

| Field | Value |
|---|---|
| `provider` | `openrouter` — the currently implemented provider |
| `model` | Exact model ID; coder and judge must differ |
| `api_key` | Your local API key |
| `base_url` | Leave empty for the default OpenRouter endpoint |

Temperature defaults to zero. Use optional `temperature_mode = "provider"` only
under an explicitly approved policy. Optional `effort` and `upstream_provider`
settings are described in [ai.example.toml](ai.example.toml).

The following command makes real API calls and reports each role's connection:

```powershell
uv run python -m unity_coder.ai_check
```

Keep credentials in `ai.local.toml`; do not put them in contracts or evidence.

## 3. Unity demonstration

Use an already-open, dedicated verification host with resolved packages and the
game-local verifier installed. Coding worktrees belong outside its imported
directories. This example specifically expects `Assets/JJGame/monopoly` and the
existing Unity Operator HTTP Bridge; it is not a generic project installer.

Set local selectors, replacing the placeholder strings:

```powershell
$env:UNITY_HOST = '<dedicated-unity-project>'
$env:DEMO_ROOT = '<new-empty-external-demo-directory>'
$env:UNITY_BRIDGE_PORT = '<bridge-port>'
$env:DEMO_ATTEMPT = '<unique-attempt-id>'
```

Read [the isolated demo instructions](examples/isolated_demo/README.md) first.
Preparation writes a synthetic fixture overlay in the dedicated host; it does
not select existing game tests. Use a separate authorized host/fixture when an
earlier demonstration or review candidate must remain intact.

```powershell
uv run python examples/isolated_demo/run.py prepare
uv run python examples/isolated_demo/run.py demonstrate
```

This deterministic two-unit rehearsal demonstrates Red, shared failure routing,
Green and Refactor confirmation without paid model calls. Evidence is under
`DEMO_ROOT`; inspect `summary.json` and the associated results.

For the exported production graph with real coder/judge calls, use a separately
prepared fresh fixture and configured models:

```powershell
uv run python examples/isolated_demo/production_graph.py
```

Expected automated success is `awaiting_human_review`. This diagnostic harness
deliberately cannot authenticate approval. Do not use its `DEMO_RESUME` switch
as automatic recovery: reconcile prior effects and uncertain usage first.
For presentation preparation and review, see the separate
[visual baseline guide](examples/visual_baseline/README.md).

## 4. Feature workflow

The Architect is Codex using OpenSpec outside the LangGraph execution boundary.
Load the maintained [framework-architect skill](.agents/skills/framework-architect/SKILL.md)
to bootstrap a fresh session with the framework's current instructions. It locates
the framework checkout, reads its authoritative docs, and routes handoff mechanics
through framework-apply. It does not install or automatically configure a target
execution host.

Example invocation:

```text
$framework-architect
Framework checkout: <framework-root>
Target project and allowed module: <target-root>, <allowed-module>
Existing OpenSpec change or feature: <change-name-or-feature-description>
Design sources: <design-and-visual-reference-locations>
Prepare the baseline and validated execution handoff; show readiness before execution.
```

For an existing run, ask the same skill to inspect and resume `<run-id>` with its
existing state root and budget. To execute new work, explicitly request preparation
and execution through the configured dedicated host. The skill is available in
this checkout; for other workspaces install its folder under your Codex skills
directory or supply the skill file directly. A global copy still needs the framework
checkout location (or the optional `FRAMEWORK_ROOT` environment variable). Keep
installed copies in sync with the versioned skill when it changes.

1. **Plan:** use `$openspec-explore` and `$openspec-propose` in the target's existing
   OpenSpec project. Resolve design/wiki/rule conflicts before export.
2. **Prepare:** have the Architect create compilable shells, explicit bindings,
   placeholder artwork and the scene/prefab baseline. Validate and identify the
   actual assets before freezing the contract.
3. **Handoff:** use the maintained
   [framework-apply skill](.agents/skills/framework-apply/SKILL.md) to export
   planning provenance and map tasks/tests/units. Runtime contracts live beside
   `spec.md` at `specs/<feature>/contract.v<N>.json`.
4. **Execute:** the trusted host composes the executor and calls
   `unity_coder.cli.invoke_local(boundary, executor)`. It supplies the run lease,
   persistent budget, isolated workspaces, model workers, blocking verifier,
   preflight and authenticated review gate. Test preparation/review/Red precedes
   global test freeze and implementation dispatch.
5. **Review:** inspect the exact verified candidate. Implementation defects repair
   within the contract; layout or requirement changes return to the Architect for
   a consecutive contract version, retaining the same run budget.
6. **Finish:** after explicit human acceptance, have the trusted host call
   `services.confirm_constraints(request, entries)` for any confirmed learned
   constraints before resuming finalization. Complete provenance and reconcile
   eligible planning tasks. Verify, synchronize specs and archive through OpenSpec.

There is currently no standalone shell `run` command that constructs a production
host from contract JSON. [production_graph.py](examples/isolated_demo/production_graph.py)
demonstrates composition for the isolated fixture; a real target must supply its
own preflight, materialization and human-authentication integration.

## 5. Progress and review

Inspect supported command arguments without contacting models or Unity:

```powershell
uv run python -m unity_coder.cli --help
uv run python -m unity_coder.cli export-context --help
uv run python -m unity_coder.cli status --help
```

The [framework-apply guide](.agents/skills/framework-apply/SKILL.md) provides full
export/status command templates. Run records live under
`<state-root>/.agent/runs/<run-id>/`: `status.json` and `progress.jsonl` describe
activity; `result.json` records the outcome; review and dossier records retain
decisions and evidence. The status response also exposes `review_package` with candidate-bound launch
and interaction guidance. Progress alone is never acceptance.

| Outcome | Next step |
|---|---|
| `awaiting_human_review` | Review the identified candidate and submit an authenticated decision |
| `rework` | Architect revises the contract from the dossier, keeping the run ID and budget |
| `operational` | Reconcile tooling, effects and uncertain usage before explicit resume |
| `cancelled` | Inspect retained work; cancellation is not a pass |
| `abandon` | Inspect budget/dossier evidence; do not reset accounting to continue |
| `pass` | Reconcile accepted task evidence, then proceed with planning-level completion |

Use `ProductionExecutor.request_cancel()` from the trusted host to request
cancellation. Already-active operations must settle before the cancelled result.

The implementation checklist is complete. Combined live production acceptance
still has the limits recorded in [verification.md](openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/verification.md):
the model-driven demo awaits human review, and its live accepted constraint flush
has not been demonstrated. Separate visual-demo approval does not approve that run.
