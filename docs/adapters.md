# Adapters: what varies per stack

The frame is stack-agnostic. Everything Unity- or C#-specific lives behind an
adapter, and this document is the line between the two.

Any Unity reference inside core logic is a bug, not a shortcut.

## What an adapter must supply

```
StackAdapter
  normalise_path(p)                  -> ownership comparison key
  is_generated(p)                    -> exclude toolchain output from enforcement
  parse_check(files)                 -> rung 2 violations
  check_interfaces(files, ifaces)    -> signature conformance
  compile(project_root)              -> CompileResult        (rung 3)
  run_tests(project_root)            -> TestResult           (rung 4)
  resolve_test_symbol(test_id)       -> (file, symbol)       acceptance -> unit
  lock_scope(project_root)           -> whole project | per dir | none
  cost_profile()                     -> expected gate duration
```

## What actually varies

| Concern | Varies by | Why it matters |
|---|---|---|
| Path comparison | Windows case-insensitive, Linux case-sensitive | collision detection must use the adapter's rule, never a hardcoded lowercase |
| Generated files | Unity `.meta`, MSBuild `obj/`, `*.g.cs`, `*_generated.*` | must be exempt from ownership enforcement or `integrate` rejects the toolchain's own output |
| Rung 2 grammar | one tree-sitter grammar per language | |
| Rung 3 command | `dotnet build`, `tsc --noEmit`, `pyright`, `cargo check`, `clang -fsyntax-only` | |
| Rung 4 runner | Unity Test Runner, `dotnet test`, `vitest`, `pytest`, `ctest` | |
| Test id format | `Class.Method`, `file.py::test_name`, `Suite > test`, `[Fact]` names | `acceptance` -> unit attribution depends on parsing this |
| Concurrency lock | Unity holds `Library/` exclusively; most stacks allow parallel builds | single-writer is an adapter fact, not a frame rule |
| Gate cost | Unity 60–120 s; `tsc` 2–5 s; `cargo check` varies | sets `k` and the budget ceilings |

## Known adapters

| Stack | Rung 2 | Rung 3 | Rung 4 | Lock |
|---|---|---|---|---|
| Unity / C# | tree-sitter-c-sharp | `dotnet build` | Unity Test Runner, batchmode | whole project, exclusive |
| .NET console / lib | tree-sitter-c-sharp | `dotnet build` | `dotnet test` | per directory |
| Node / TypeScript | tree-sitter-typescript | `tsc --noEmit` | vitest / jest | per directory |
| Python | tree-sitter-python | `pyright` or `mypy` | pytest | per directory |
| C++ / CMake | tree-sitter-cpp | build (no separate syntax gate) | ctest | per build dir |

The Unity adapter is the first planned implementation. The others are listed to keep
core honest: if a rule cannot be expressed for two different rows of that table, it
is not a core rule.

## Adopted adapter refinements (D-24, D-25, D-27)

Adapter evidence also covers protected manifests and serialized binding interfaces.
Generated files remain ownership-exempt but cannot escape scope or alter frozen
asset identities/import settings. Core consumes generic violations and hashes;
Unity GUIDs, scene serialization, grammars, host commands, and import checks never
live in core. Test-symbol resolution returns relationships, not a guaranteed culprit.

The first target uses Tuanjie 1.9.2 / Unity 2022.3.62t10, HybridCLR, an independent
game repository mounted at Assets/JJGame/monopoly/, and existing Unity Operator
HTTP tooling. These are target profile inputs, not universal adapter defaults.
Preserve jj.Reserve04.Runtime, module entry/DI identities, permitted bifrost
interfaces, teardown, serialization, platform rules, Navigator/VVMP, resource
addresses/bundles, generated-code boundaries, and _placeHolder art naming.
Read game AGENTS/rules, Docs~/ source/wiki, .codex/reference/, and existing OpenSpec
before export; hash the relevant rules and source provenance.

Coding and integration are external module worktrees; they contain no complete
Unity host. The worker owns a dedicated full project with pinned nested-module
revisions, packages/settings, and exactly one game candidate. Source and delivered
content writes stay inside the game boundary; only configured transient caches,
logs, and request evidence are operational outputs. Preserve the user's editor
project and detect shared-host drift. Never put unit worktrees under Assets/.

For this target, reuse cn.jj.unity-operator behind blocking VerifyTransport. Its
HTTP health endpoint verifies exact project identity; polling stays inside the
worker. Add an owned game-local IUnityOpCommand/TestRunnerApi integration instead
of changing the shared package. Refresh/reload, command submission, nested command
success, compilation, and test completion are separate evidence. Task IDs are
memory-local; durable request/candidate identities and callbacks govern results.
No live Bridge connection, compile inclusion, or actual test success has yet
been established. Batchmode remains a separately validated future backend.

## Core versus adapter

**Core** (same for every stack): contract schema, ownership freeze, test freeze,
defect classification, two loops, trend predicates, budget arithmetic, branch
model, `AGENTS.md` managed block, dossier format.

**Adapter** (differs per stack): path semantics, generated-file exclusions, parse
grammar, compile and test commands, test-symbol resolution, lock scope, cost
profile.

## Five things generalising exposed

These were latent bugs in the Unity-only sketch. Each is now an adapter
responsibility rather than an assumption baked into core.

1. **Path normalisation must not lowercase.** The scaffold normalised paths with
   `str(Path(p)).lower()` to cope with Windows. That silently merges `Queue.cs` and
   `queue.cs`, which are two different files on Linux. Case folding is a Windows
   adapter rule; on a case-sensitive adapter it is a correctness bug.
2. **Generated sidecar files need an exemption.** Unity writes a `.meta` beside
   every new `.cs`. If ownership enforcement does not exempt generated files,
   `integrate` will reject the editor's own output the first time a unit creates a
   file.
3. **`acceptance` -> unit attribution is not universal.** Unity names tests
   `Class.Method`; pytest names them `file.py::test_name`; C# `[Fact]` names are
   attributes. The dossier's self-attribution property depends on the adapter's
   `resolve_test_symbol`, so it cannot live in core.
4. **Single-writer locking is Unity's constraint, not the frame's.** Most stacks
   compile in parallel. The run-scoped lock stays in core, but its *reason* changes:
   it protects integration ordering everywhere, and additionally works around a
   single-writer toolchain only for Unity.
5. **Budget defaults cannot be shared.** A 90-second Unity gate and a 3-second
   `tsc` gate cannot justify the same `k` or the same token ceiling. The formula in
   `loop-control.md` is core; the constants are per adapter.

## Open items

Phase 2 offline implementation uses tree-sitter-c-sharp to reject error/missing
nodes and compare declared class, method, and field signatures. Qualified or
class-relative method symbols support overload signatures; formatting/body
changes do not change a signature. Serialized field contracts can include
`[SerializeField] int score`, so renaming, type changes, or attribute removal fail.
Violations carry file, symbol, code, and a concise diagnostic. This is structural
conformance, not proof of runtime binding or Unity import health.

Generated-path classification is adapter policy. It does not skip conformance
on generated source or authorize protected presentation writes. The first
adapter reports an operational error for compile/test calls until the Phase 6
transport is configured; it cannot return a placeholder passing result.

- Only the Unity adapter is specified. The second adapter (whichever stack comes
  next) is the real test of whether this boundary is drawn correctly — expect it to
  move at least one rule out of core.

## Dedicated host synchronization acceptance

The worker materializer requires a provisioned complete host and an empty initial
game mount. Provision shared modules, packages, and settings separately; pass the
fixed nested revision map and a revision probe. The mount cannot contain links.
The durable .agent/materialization.json manifest binds mount, assembly, host file
hashes, dependencies, candidate identities, and previously managed game files.
Only stale manifest entries are deleted. Unmanaged content stops synchronization;
it is never adopted or cleaned automatically. Interrupted writes fail closed for
controlled reprovisioning. Library/, Logs/, and Temp/ are default operational
outputs; additional exclusions cannot overlap Assets, Packages, or ProjectSettings.

Keep the worker host lease throughout synchronization, import, and every gate.
Call capture_import after import and assert_ready around gates. New game-local
metadata must be included verbatim in a new coordinator candidate; existing
metadata/content changes fail. Restart verification with that candidate identity.
These offline component checks do not establish live editor import or compilation.

## Observed target profile (2026-11-16)

Portable read-only source identities are recorded in
../openspec/changes/archive/2026-11-18-formalize-unity-feature-delivery/target-provenance.json.
The 53 SHA-256 entries cover game rules, knowledge indexes, the existing OpenSpec
source register, original Docs~/Design documents, assembly/loader/package files,
and host package/settings manifests. Revalidate them before exporting any feature;
this observation is not permission to reinterpret or modify original designs.
Keep the game's existing planning system. Feature-specific source conflicts and
bindings still belong to its Architect export, not a second game specification.

The inspected host uses Tuanjie 1.9.2 / Unity 2022.3.62t10 (94a36fdd07ef), installed
cn.jj.unity-operator@0.0.1, and com.unity.test-framework@2.0.1-exp.2. The runtime
assembly is jj.Reserve04.Runtime; Reserve04ModuleLoader registers IReserve04 to
Monopoly and pairs unloading with DestroyServicesOfModule. Editor code is in
jj.Monopoly.Editor. jj.Monopoly.Tests.Runtime is Editor-only and constrained by
UNITY_INCLUDE_TESTS. Resource keys begin after Runtime/Resource/ and use monopoly;
reuse the existing Root scene, binding tools, PSD pipeline, and AssetGraph rules.

Runtime policy prohibits unmanaged static state, direct cross-module concrete
implementation dependencies, AOT-to-hotfix references, unsupported interop, and
unpaired lifecycle subscriptions. Preserve MonoBehaviour message signatures,
serialized custom arrays, Newtonsoft serialization, framework filesystem and
WebGL async resource APIs. Use existing bifrost, Navigator/VVMP, event, scheduler,
resource, and pool capabilities before introducing alternatives. Placeholder
identities and _placeHolder naming are part of the asset contract.

The packaged FrameworkVerify helper must be installed only in the dedicated
host's game-local Editor/test assembly with references to Unity Operator,
UnityEditor.TestRunner, UnityEngine.TestRunner, and the installed Newtonsoft
assembly. Assembly reference resolution and new-file inclusion require live
validation; syntax parsing does not prove either. Durable request/result files
live under .agent/verification/<ticket>/ outside Assets. The helper does not
start an editor, install a package, or exit the user's editor. A lost/uncertain
submission remains pending for reconciliation and is never submitted twice.

The live Bridge may return an empty health command list because its HTTP-thread
scene query throws before enumeration. The worker first verifies project identity,
then reads main-thread project_info and queries the game-local, side-effect-free
FrameworkVerifyCapabilities command. Protocol 1, FrameworkVerify, and both compile
and tests modes are required. This does not install tooling or submit a test as a
probe; missing/incompatible capabilities remain operational failure.

## Architect presentation preparation (task 10.3)

`unity/Editor/FrameworkVisualPreparation.cs` is an Architect-only preparation
fixture, installed in its own game-local Editor assembly. It creates the isolated
FrameworkVisualDemo scene/prefab, compilable preview shell and `_placeHolder`
sprite using existing Unity APIs. It reuses the installed target's read-only
PsdPrefabLayoutAutomation inspector. This synthetic brief has no PSD or map;
their existing converters and assets are left intact rather than recreated.
Actual game features continue to use their existing source/conversion tooling.

Preparation refuses to overwrite destinations. Inspection records protected file
hashes, hierarchy, explicit serialized field targets, persistent button listeners,
sprite import settings, missing scripts and successful review-scene loading.
Existing scenes are not saved or overwritten. The preview changes only status
text/color and has no game bootstrap or business behavior. Runtime assets follow
the target UI/Images, UI/Prefabs and Scenes conventions; author references live
in the isolated Editor/ArtSource~ folder. Original Docs~ stays untouched.

The trusted editor supplies PreparedBaseline observations. freeze_prepared checks
them against disk and constructs the existing generic Presentation manifest;
the Unity validator then checks C# interfaces and imported identities. Export
preserves the same bytes and metadata in an external game preparation worktree.
No coder can invoke this builder or regenerate a frozen presentation. Human
approval remains a separate revision-bound gate; preparation is not acceptance.

Tuanjie can serialize encoded GUIDs in metadata while AssetDatabase returns
canonical GUIDs. ImportReport and PreparedBaseline therefore optionally carry
serialized_asset_ids alongside asset_ids. The trusted editor must verify
GUIDToAssetPath round-trip before supplying that mapping. Both the canonical
identity and the exact serialized token are checked; frozen metadata hashes
remain mandatory. Without that explicit mapping, differing identities fail.
Plain Unity metadata retains the original direct equality rule.

See examples/visual_baseline/README.md for the launch instructions, environment
selectors and preparation sequence. ArtistAsset records the reference, purpose,
dimensions, transparency, variants, import settings, usage and later replacement
criteria. The observed fixture is a reviewable baseline, not game feature
acceptance, final art, or an automated PlayMode policy.
