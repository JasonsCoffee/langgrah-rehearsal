# Dev environment

Setup for the LangGraph side, on the Architect's Windows workstation, alongside
Unity. The original toolchain observations below date from 2026-11-12 and are
historical, not installation guarantees on a different workstation. On 2026-11-16,
`uv --version` reported 0.5.27 and `uv python list --only-installed` confirmed
managed CPython 3.12.11. Use the Python 3.12 pin and the committed lockfile;
record actual resolution and smoke checks when provisioning a machine.

Sections 1–4, 7 and 9 are stack-neutral. Sections 5, 6, 8 and the Unity variables
in `.env` belong to the Unity adapter; a second stack replaces them with its own
compile and test commands (see `adapters.md`).

## Historical toolchain observations (2026-11-12)

| Tool | Version | Verdict |
|---|---|---|
| uv | 0.10.10 | use it; no Python install needed |
| uv-managed CPython | 3.12.13 | **pin this** for the project |
| system Python | 3.14.3 | do not use for this project |
| .NET SDK | 10.0.301 | rung 3 (`dotnet build`) is viable |
| git | 2.55.0 | fine |
| Node | 22.22.2 | not needed |
| Docker | absent | `langgraph dev` does not need it |

Note: the dependency set resolves on 3.14 as well, but 3.12 is what the
ecosystem's wheels and CI are proven against, and this project is meant to live
for months. Pin it rather than inherit whatever is on `PATH`.

## 1. Pin the interpreter

```bash
cd <graph project>
uv python pin 3.12          # writes .python-version
uv venv --python 3.12
```

Reason: the system Python will drift under you (a global upgrade, a Unity-installed
runtime, a tool that ships its own). A pinned interpreter makes the project
reproducible six months from now.

## 2. `pyproject.toml`, not `requirements.txt`

```toml
[project]
name = "unity-coder"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "langgraph>=1.2",
  "langgraph-cli[inmem]>=0.4",
  "tree-sitter>=0.26",
  "tree-sitter-c-sharp>=0.23",
]

[dependency-groups]
dev = ["pytest>=9,<10"]

[tool.uv]
package = true
```

```bash
uv sync
```

Two things that matter here:

- **`langgraph-cli[inmem]`** — the `inmem` extra is what makes `langgraph dev`
  work without Docker. Without it the command is unavailable.
- **`tree-sitter-c-sharp`** — rung 2 of the ladder parses C# with no Unity and no
  Roslyn. This is a runtime dependency, not a dev tool.

Versions verified to resolve together:

```
langgraph 1.2.20   langgraph-cli 0.4.42   langgraph-api 0.17.1
langchain-core 1.8.0   pydantic 2.14.3   langsmith 0.14.17
tree-sitter 0.26.1   tree-sitter-c-sharp 0.23.5
```

The current pyproject uses the setuptools build backend for editable installation.
Provider SDKs and optional debugger dependencies belong to their later milestones.
Installing the local package in editable mode is
required because `langgraph.json` points at `./src/unity_coder/graph.py:graph` and
the nodes import `unity_coder.*`.

## 3. `.env` and `langgraph.json`

AI configuration now has a separate local template: fill `ai.local.toml`, which
is ignored by Git. `ai.example.toml` is the shareable blank template. Both coder
and judge require `provider`, `model` and `api_key`; `base_url` is optional for a
custom endpoint. Use different model identities; temperature defaults to zero.
D-28 permits explicit `temperature_mode = "provider"` for an approved judge,
omitting the unsupported temperature parameter. Optional `effort` preserves the
chosen reasoning effort. The model boundary
loads this file explicitly; graph startup does not make provider requests.
Run `uv run python -m unity_coder.ai_check` for a short opt-in connectivity probe.
The model/API-key variables in the earlier `.env`
example below are superseded for this setup. Keep host and tracing settings in
`.env`.

The implemented provider is OpenRouter, using its documented
[Chat Completions endpoint](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request).
Requests require support for the supplied parameters and disable provider
fallbacks. A model that cannot honor temperature zero requires explicit approval
of provider-controlled temperature; connectivity failure alone does not authorize
either that exception or a model substitution.
Transport errors omit response bodies and credentials, have bounded timeouts,
and do not trigger automatic paid retries. `ModelCalls` reserves budget before
dispatch, records intent, persists replies before reconciling actual usage, and
retains uncertain reservations across restart. Production executor integration
remains a separate acceptance requirement.

```bash
# .env  (gitignored) - copy from .env.example, fill in on each machine
UNITY_CODER_MODEL=anthropic:claude-sonnet-4-5
JUDGE_MODEL=openai:gpt-5
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langgraph-coding-framework
UNITY_PROJECT_ROOT=<path to the Unity project on this machine>
UNITY_EXE=<path to Unity.exe, or leave empty>
UNITY_HUB_ROOT=<path to the Hub Editor folder, or leave empty>
```

Two separate model variables on purpose: the judge must run on a different model
from the coder (`decisions.md` D-12).

Unity discovery order: `UNITY_EXE`, then `UNITY_HUB_ROOT`, then
`%PROGRAMFILES%/Unity/Hub/Editor`. The last hop picks lexicographically, which is
not "newest" once you hold more than one version — set `UNITY_EXE` explicitly when
the project pins a Unity version. No machine-specific path is hardcoded anywhere in
the repository, because it is meant to be copied between machines.

`langgraph.json` stays as it is — `"dependencies": ["."]` and `"env": ".env"`.

## 4. Optional LangSmith account

Tracing is optional. Local graph compilation, listing, and the offline suite must
work without provider or tracing keys. Durable local status and evidence remain
the source of execution truth; remote traces are a debugging aid.

## 5. Run the dev server

```bash
uv run langgraph dev --allow-blocking
```

Gives you the API on `127.0.0.1:2024`, hot reload, and Studio in the browser.

**`--allow-blocking` is not optional for this project.** `langgraph dev` raises an
error on synchronous blocking I/O by default. The verify node shells out to
`dotnet build` and then Unity for 90 seconds or more, which the dev server will
reject without this flag. In production the blocking call is correct — it is what
keeps the loop closed — so the flag stays a dev-mode concession, not a design
change.

## 6. Attach a debugger

```bash
uv add --dev debugpy
uv run langgraph dev --allow-blocking --debug-port 5678
```

`.vscode/launch.json`:

```json
{
  "name": "Attach to LangGraph",
  "type": "debugpy",
  "request": "attach",
  "connect": { "host": "127.0.0.1", "port": 5678 }
}
```

Step debugging inside a node is how you will actually find state-reducer bugs. They
are invisible in logs because the value is correct in the node and wrong after the
merge.

## 7. Keep the graph project outside the Unity project

Not a style preference:

- `langgraph dev` watches the project tree for hot reload. Nest the graph inside a
  Unity project and the watcher sees `Library/` — tens of thousands of files — and
  reloads continuously.
- Coding units write only owned implementation/test files in external module
  worktrees. Accepted completion additionally flushes one managed convention
  block; planning inputs remain read-only to execution (D-26).

The current layout already does this.

## 8. Prepare external coding worktrees and a complete verification host

The first target is an independent game repository mounted at
`Assets/JJGame/monopoly/` in a larger Unity project. A module worktree is not a
Unity project; an outer repository checkout alone does not populate nested repos.
Provision a dedicated complete host at an authorized location, recording every
required nested revision and package/settings identity before using it. Keep the
user's interactive project unchanged. Never put coding worktrees beneath Assets.

```text
game baseline -> external test worktrees -> reviewed Red -> frozen tests
              -> parallel external implementation worktrees
              -> coordinator integration revision
              -> blocking worker -> complete fixed host / one game mount
              -> sequential EditMode -> full suite -> human review
```

Architect preparation uses the existing game's OpenSpec, `Docs~/` original
designs/wiki, and `.codex/reference/` API evidence. Export hashed source provenance
and coding rules. Preserve the target assembly/resource conventions documented in
adapters.md. Coding tools cannot mutate other worktrees, shared Git metadata, or
the editor; worktrees alone do not enforce these restrictions.

Only the worker materializes candidates into the host's single game mount,
preserving tracked metadata and deleting only stale previously managed files.
Reject links escaping the mount and shared-host drift. Reconcile import-generated
metadata into the candidate before gates; permit only configured caches, logs,
and request evidence outside delivered game content. Keep the snapshot fixed
for the whole ladder and acquire exclusive access to the host.

The installed `cn.jj.unity-operator` provides HTTP, not MCP. Validate the exact
host identity through bounded discovery; use a game-local `IUnityOpCommand` with
`TestRunnerApi` callbacks and durable request-specific evidence. Refresh, nested
command success, compilation, and test completion are distinct states. Reconcile
Domain Reload and lost Bridge task IDs before any retry. Do not install a shared
package or launch another editor to mask missing connectivity. Installed source
has been inspected; live connectivity, new-file compile inclusion, and real tests
remain unverified. Batchmode is a separately validated future transport.

## 9. Windows tuning

- **Defender exclusions** for `.venv`, and the Unity project's `Library/`, `Temp/`,
  `obj/`. Real-time scanning on `Library/` is one of the largest silent slowdowns
  in a Unity workflow, and it compounds with a 90-second verification gate.
- **Long paths**: `git config --global core.longpaths true`. Unity plus a nested
  venv comfortably exceeds `MAX_PATH`.
- **Do not** put the graph project in a synced folder (OneDrive, Dropbox). Sync
  conflicts on `.venv` and `uv.lock` are painful to unwind.

## 10. What the environment must support

The design requires that rungs 1 and 2 be testable **on a machine with no Unity at
all**. So the environment needs:

- `pytest` with no network access in tests — a fake model client, not a real one
- a `FakeTransport` implementing `VerifyTransport`, so ladder tests never touch Unity
- `tree-sitter-c-sharp` importable standalone

If a test needs Unity or a provider key, the boundary has leaked into the code.

## 11. Sanity sequence

Run these in order before writing pipeline code:

```bash
uv run python -c "from importlib.metadata import version; print(version('langgraph'))"
uv run langgraph dev --allow-blocking        # Studio opens, graph listed
dotnet build <unity>/Assembly-CSharp.csproj  # rung 3 works at all
uv run pytest
```

Then close the two design unknowns:

1. Time one `dotnet build`. Confirms the compile gate is 5–10 s or not (and whether
   new-file csproj inclusion is a problem — check by adding a new `.cs` and
   rebuilding).
2. Time one EditMode run on the real project. This sets the cycle budget in
   `loop-control.md`.

## Live compile inclusion

Live acceptance update: the Bridge compile backend includes new files. Running
`uv run python examples/isolated_demo/compile_inclusion.py` against the authorized
dedicated host added a temporary source with a unique #error marker. Its failed
compile callback arrived 1.092 seconds after request creation. Cleanup removed
only that owned source and its generated metadata. A ParrelSync promotional dialog
blocked reload and caused a recovery timeout; after closing it, a fresh compile
callback passed in 0.790 seconds and all five isolated tests passed. These callback
timings exclude import, reload and dialog time; they are not full ladder timings.
The exact pre-probe snapshot was restored. Evidence and the retained timeout are
under the active change's live-evidence/compile-inclusion/. No csproj fallback is
needed for this validated Editor compile backend; this does not validate dotnet.

## Deliberately not set up

| Thing | Why not |
|---|---|
| Docker | only needed for `langgraph build` / `up`, which is a deployment concern |
| LangSmith Deployment | running locally with durable local state and evidence |
| Node / LangGraph.js | the graph is Python; Node is present but unused |
| A second machine | decided in `decisions.md` D-17 — co-locate for v0 |
