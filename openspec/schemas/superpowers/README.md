# Superpowers schema

Project-local OpenSpec workflow adapted from
[obra/superpowers](https://github.com/obra/superpowers). This is a schema-level
integration of its development practices, not an installation of the upstream
skills or plugin. The schema is self-contained and needs only the pinned OpenSpec
CLI. Its starting point is OpenSpec 2.0.0's `spec-driven` schema.

The artifact dependency chain is:

`brainstorm -> proposal -> specs -> design -> tasks -> apply`

Brainstorming captures intent, alternatives, and decisions. Design maps the chosen
approach to the frozen architecture. Tasks capture small steps, test-first
evidence, the test freeze boundary, and two passes of review. Apply includes
root-cause investigation for failures and fresh evidence before completion.

The apply instructions require a `verification.md` report inside the change
directory. It is an execution output rather than a prerequisite artifact: making
it a prerequisite would require verification evidence before implementation.
Include its creation and review in the tracked tasks. Artifact presence and
checkboxes cannot prove that tests ran, reviews happened, or tests stayed frozen;
these remain agent obligations and framework enforcement responsibilities.

Repository adaptations take precedence over upstream conventions:

- `docs/` remains authoritative; settled decisions require a superseding decision.
- Tests are frozen for the cycle before implementation starts. Implementers return
  test or contract defects to planning rather than editing frozen tests.
- Planning artifacts stay under `openspec/changes/`, not the upstream default
  documentation locations. Runtime contracts keep their existing layout.
- No automatic commits, pushes, merges, worktree removal, or agent delegation.
- Reviews run inline unless separately authorized; self-review is identified.
- Framework phase completion requires the repository's specified acceptance
  checks. Tooling-only work uses relevant validation and claims no phase complete.

## Use and validate

`openspec/config.yaml` selects `superpowers` for new changes. Existing changes keep
their recorded schema. Use the installed OpenSpec workflows normally, or create
a change explicitly with `pnpm exec openspec new change <name> --schema superpowers`.
Then use `openspec-continue-change` for one artifact at a time or
`openspec-ff-change` for planning artifacts together, followed by
`openspec-apply-change` for implementation. Planning alone never supplies runtime
verification evidence.

Validate with `pnpm exec openspec schema validate superpowers --json` and inspect
resolution with `pnpm exec openspec schema which superpowers --json`.
`pnpm run openspec:refresh` regenerates skills but leaves this local schema intact.

## Upstream references

- [Brainstorming](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md)
- [Writing plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md)
- [Test-driven development](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md)
- [Systematic debugging](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md)
- [Requesting code review](https://github.com/obra/superpowers/blob/main/skills/requesting-code-review/SKILL.md)
- [Verification before completion](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md)
