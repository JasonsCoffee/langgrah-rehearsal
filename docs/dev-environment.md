# Dev environment

Setup for the LangGraph side, on the Architect's Windows workstation, alongside
Unity. Everything below was resolved against the toolchain currently installed on
this machine (2026-11-12).

Sections 1–4, 7 and 9 are stack-neutral. Sections 5, 6, 8 and the Unity variables
in `.env` belong to the Unity adapter; a second stack replaces them with its own
compile and test commands (see `adapters.md`).

## What is already present

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
  "langchain>=1.0",
  "langchain-anthropic",
  "tree-sitter>=0.26",
  "tree-sitter-c-sharp>=0.23",
  "python-dotenv>=1.0",
]

[dependency-groups]
dev = ["pytest>=9", "pytest-asyncio", "debugpy"]

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

`[tool.uv] package = true` installs the local package in editable mode, which is
required because `langgraph.json` points at `./src/unity_coder/graph.py:graph` and
the nodes import `unity_coder.*`.

## 3. `.env` and `langgraph.json`

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

## 4. LangSmith account

Free tier is enough. Without it you lose Studio and tracing, and tracing is the
only practical way to debug a graph with cycles, fan-out, and interrupts —
`print` does not scale to a run that fans out to six coders across three cycles.

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
- The boundary says the graph writes exactly one managed block into the repo.
  Keeping the code in a separate directory makes that boundary physical rather
  than merely stated.

The current layout already does this.

## 8. Prepare a verification worktree

`Library/` is single-writer, so batchmode cannot run against the project while the
editor has it open. Create a second copy to verify against:

```bash
cd <path to the Unity project>
git worktree add ../verify-wt main
```

Point `--project-root` at `../verify-wt` when verifying while you are working in the
editor. Cost: the first import in a fresh worktree takes minutes and the copy costs
disk; reap worktrees older than a few days.

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
uv run python -c "import langgraph, tree_sitter; print(langgraph.__version__)"
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

## Deliberately not set up

| Thing | Why not |
|---|---|
| Docker | only needed for `langgraph build` / `up`, which is a deployment concern |
| LangSmith Deployment | running locally for now; the graph is a pure function of `(contract, run_id)` |
| Node / LangGraph.js | the graph is Python; Node is present but unused |
| A second machine | decided in `decisions.md` D-17 — co-locate for v0 |
