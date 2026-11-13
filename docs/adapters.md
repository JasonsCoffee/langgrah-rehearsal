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

The Unity adapter is the only one implemented today. The others are listed to keep
core honest: if a rule cannot be expressed for two different rows of that table, it
is not a core rule.

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

- Only the Unity adapter is specified. The second adapter (whichever stack comes
  next) is the real test of whether this boundary is drawn correctly — expect it to
  move at least one rule out of core.
