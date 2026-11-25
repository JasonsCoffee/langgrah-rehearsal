# Monopoly Lobby rehearsal handoff

Checkpoint recorded 2026-11-25, Asia/Shanghai.

## Start here

The existing run is `monopoly-game-lobby`. Contract **94** ended in
`rework` on retained candidate
`06b2397ae92818d1efb9057b3455aaba2c195082`. The contract SHA-256 is
`679673209540c51dffa56408841f516527f5f0846e1d39547adc6feba6689cdc`.
The architecture input checkout for that cycle starts at
`ff36fa19258665a744716909f702bd2ee8ab0f7b`. Use the native `result.json`
for the retained candidate and `current-execution.json` for its architecture
input. The two files serve different purposes.

The latest candidate has nine of sixteen test suites approved in source review:
Appearance, Cards, Chat Message, Harness, Match, Presentation Core,
Presentation NFR, Queue, and VIP. The freeze guard protected 228 other
source files during the Match correction. Fifty-three focused offline
framework and rehearsal checks passed during the continuation. Earlier
runtime implementation and Unity evidence remain historical. Fresh Unity Red,
the new freeze, integrated runtime verification, and human review are pending.

| Counter | Accounted | Ceiling |
| --- | ---: | ---: |
| Active period input tokens | 100,744,888 | 110,000,000 |
| Active period output tokens | 393,223 | 2,000,000 |
| Native contract cycles | 94 | 120 |
| Cumulative Codex Judge claims | 248 | 250 |

The native ledger limits, including the earlier accounting period, are
280,044,520 input and 8,520,897 output. Keep all historical charges and 28
unreconciled reservations. The native `post-backend-110m` recovery records
the previous 1,284 call entries and 92 cycles.

## Work completed

- Resolved the design against the three original Chinese source documents,
  recorded approved rehearsal choices, and mapped the stories to owned
  source, tests, and review requirements in the existing OpenSpec change.
- Prepared the original 3D street, character, vehicle, scenes, prefabs,
  catalog and fake-service baseline. Built a trusted Unity overlay with
  project identity checks, materialization hashes, import drift checks,
  and sequential EditMode verification.
- Delegated the five runtime units and retained their earlier candidates,
  compile evidence and test results. A fresh Red and freeze is required
  for the current test contract before integration can proceed.
- Configured direct DeepSeek Flash with low effort for Coder and the
  context selector, and GPT-6.1 Sol with low effort through the Codex app
  server for Judge. Added verifiable review packets, context checks and
  independent verdict receipts. Raw Coder narrative is filtered out.
- Recorded and applied approved, method-level test corrections across
  presentation, economy, chat, VIP, and Match. Bound the existing
  deterministic fake seat-allocation rule to Queue review and verified
  the requested authoring records without editing Queue tests.
- Preserved the run across cycle and budget amendments, the Judge limit
  amendment, and operational recovery. The missing Match review receipt
  from contract 91 remains fully reserved. A fresh independent review
  subsequently passed.

See [continuation status](continuation-status.md), the [proposal](proposal.md),
and [tasks](tasks.md) for the feature and decision trail.

## Git branches and machine-local inputs

| Item | Restore source |
| --- | --- |
| Planning and this handoff | `origin/codex/lobby-backend-checkpoint` |
| Executable rehearsal host, recovery helpers and focused regressions | `origin/codex/codex-worker-backend` at `a923b5cd27dfcae7f7b0f51b041c8c12927d0535` |
| Framework resilience fixes | `origin/codex/framework-resilience-fixes` |
| Isolated game Git repository | Private copy of the run directory, including `module/.git`, or the local Git bundle for commit and ref recovery |
| Live run and evidence | Private copy of the complete rehearsal root, including `trusted-state/`, `module/` and `worktrees/` |
| Dedicated Unity verification project | Private copy of the matching project source, package dependencies, and overlay state |
| Provider credential and CLI session | Reconfigure the ignored `ai.local.toml` and provision the authorized Codex login locally |

The framework remote carries the code and planning checkpoint. The isolated
game module has no configured remote. Its linked worktrees, trusted state,
Unity installation, provider credentials, and account session require a
private transfer or local provisioning. Model evidence can contain full
source and input payloads, so transfer it through an approved private channel.

### Recreate the framework checkout

Use Windows PowerShell, Git, Python 3.12 via `uv`, Node.js 22.12 or later,
pnpm, and the Codex CLI with app-server support. Clone the existing framework
remote, check out the planning branch, and run from the checkout root:

```powershell
git switch --track origin/codex/lobby-backend-checkpoint
git worktree add --track -b codex/codex-worker-backend .agent/codex-worker-backend origin/codex/codex-worker-backend
uv sync --locked
pnpm install --frozen-lockfile
New-Item -ItemType Directory -Force .agent | Out-Null
$change = 'rehearse-monopoly-game-lobby'
pnpm exec openspec instructions apply --change $change --json |
    Set-Content -Encoding utf8NoBOM .agent/lobby-apply.json
$sources = "openspec/changes/$change/sources"
[ordered]@{
    'original-0' = "$sources/大赢家主界面策划案.docx"
    'original-1' = "$sources/大赢家局外主界面-需求分析.md"
    'original-2' = "$sources/大赢家局外主界面-用户故事.md"
} | ConvertTo-Json | Set-Content -Encoding utf8NoBOM .agent/lobby-sources.json
```

The host reads the two generated JSON inputs with the framework root as its
working directory. Verify the exported source/task context matches the
existing run before dispatch. Use PowerShell 7 for `utf8NoBOM`.
If Git already has a local tracking branch, use `git switch` or
`git worktree add` with that branch.

Create ignored `ai.local.toml` in the planning checkout using this policy.
Set the key locally, and authenticate the Codex CLI separately.

```toml
[coder]
provider = "deepseek"
model = "deepseek-flash"
effort = "low"
base_url = "https://api.deepseek.com"
api_key = "<your-deepseek-key>"
max_output_tokens = 65536
```

### Restore run data and Unity

1. Stop all run drivers and the dedicated Unity Editor before copying.
   Copy the entire isolated rehearsal directory, preserving its contents
   and line endings. The source run occupies about 38 GiB, mostly trusted
   state and linked worktrees. Keep the original paths on the destination if
   practical. When paths move, repair the copied linked worktree
   registrations with `git worktree repair <new-linked-worktree-path>`
   from the copied isolated module for each moved worktree.
   Verify important paths including `worktrees/architect-v94` and
   `worktrees/monopoly-game-lobby/integration-v94`, their exact revisions
   and clean status, and any path-bound Unity and host records. Have the
   trusted host reconcile differences before resuming. Never edit
   evidence to make a path or hash check pass.
2. Keep the module Git bundle as a separate recovery copy of commits and
   refs. The verified local bundle is
   `.agent/lobby-transfer/monopoly-game-lobby.bundle` in the original
   framework checkout. Its SHA-256 is
   `ec12dd6fbc39562882f92cca9e5858e4e9b0b70570d1f424d6bed0037ca2c5fc`.
   Verify it with `git bundle verify <bundle>` from the isolated module.
   Exact resume requires the copied linked worktrees and live state.
3. Restore the dedicated project with `Assets`, `Packages`,
   `ProjectSettings`, their metadata, project-specific build inputs such
   as `HybridCLRData`, and any referenced local package sources.
   The original host uses Unity/Tuanjie **2022.3.62t10**
   (revision `94a36fdd07ef`, Tuanjie **1.9.2**). Editor caches can be
   rebuilt. Open the dedicated project and bring its verification Bridge
   up in idle Edit Mode. Port **49166** was used originally.
4. Set the selectors below. Confirm Bridge `GET /` reports the selected
   project path and is idle. Its `FrameworkVerifyCapabilities` command
   must expose protocol 1 compile and tests, with no active ticket.
   Preserve the trusted overlay and verify baseline and import drift
   before materializing a new candidate.

```powershell
$env:LOBBY_RUN_ROOT = '<restored-isolated-rehearsal-directory>'
$env:UNITY_HOST = '<restored-dedicated-Unity-project>'
$env:UNITY_BRIDGE_PORT = '49166'
$env:LOBBY_MODEL_BACKEND = 'mixed'
$env:PYTHONUTF8 = '1'
$env:PYTHONPATH = (Resolve-Path .agent/codex-worker-backend/src).Path
```

Read-only checkpoint checks from the framework root:

```powershell
$run = Join-Path $env:LOBBY_RUN_ROOT 'trusted-state/.agent/runs/monopoly-game-lobby'
Get-Content (Join-Path $run 'result.json')
Get-Content (Join-Path $run 'dossier-v94.json')
git -C (Join-Path $env:LOBBY_RUN_ROOT 'module') show -s 06b2397ae92818d1efb9057b3455aaba2c195082
Invoke-RestMethod ('http://127.0.0.1:' + $env:UNITY_BRIDGE_PORT + '/')
```

Run the backend worktree's offline tests in UTF-8 mode on Windows:

```powershell
Push-Location .agent/codex-worker-backend
try {
    $env:PYTHONUTF8 = '1'
    $env:PYTHONPATH = (Resolve-Path src).Path
    ../../.venv/Scripts/python.exe -m pytest -q
} finally {
    Pop-Location
}
```

The handoff verification ran 925 cases. Windows default GBK decoding
caused 12 failures in the UTF-8 evidence fixtures, and the other 913
passed. The entire affected test file passed on a UTF-8 rerun (22 cases).

The native driver is
`.agent/codex-worker-backend/openspec/changes/rehearse-monopoly-game-lobby/lobby_production_host.py`.
Run it from the planning checkout with the selected backend on
`PYTHONPATH`, after an authorized native transition or operational recovery.
It can dispatch paid calls and drive Unity. The current cycle is parked in
`rework`.

## Next decision and execution

Contract 94's independent Party review identified two gaps in
`Tests/Runtime/Script/LobbyRehearsal/LobbyMatchPartyTests.cs`:

1. `Story_L11_04` needs to enter the busy recipient's UI session before
   attempting the invite and verify the invitation surface remains absent.
2. `Story_L11_07` needs to associate each diagnostic with its own rejected
   start or queue identity so an unrelated fresh failure cannot satisfy it.

Approval to edit only these two methods was requested and is pending at this
checkpoint. Upon approval, record it in the trusted host and use a consecutive
native contract transition. Keep the reviewed Match patch and every other
protected file intact. Use Coder to make the scoped correction and Judge for
independent source review. Only two Judge claims remain at this checkpoint.
Any increase needs separate authorization. Monitor the token ledger and native
review reservations as well.

After source reviews pass, run fresh Unity EditMode Red on the contracted
selection. Establish behavioral failure against the baseline, then freeze and
run delegated integration and verification. At `awaiting_human_review`, share
the exact candidate and evidence for the requested Lobby interactions. Human
approval remains a separate explicit step.
