---
name: framework-apply
description: Prepare a portable Architect handoff from an existing OpenSpec change and inspect delegated execution evidence.
---

# Delegated framework apply

This maintained skill supplements the installed OpenSpec skills. Do not edit
generated skills or introduce a custom schema. Planning authority stays with the
Architect; the executor cannot update planning checkboxes.

## Discover existing planning

Use the project's pinned OpenSpec CLI. In this repository that is
`pnpm exec openspec`. Select the existing project/store and keep its selection
on subsequent commands. Run `list --json`, `status --change <change> --json`,
and `instructions apply --change <change> --json`. Do not initialize a new root.
A missing root, unresolved store, or blocked apply state must be resolved first.

Read every file in the returned `contextFiles`, using its artifact IDs rather
than assuming proposal/design/tasks filenames. Read required `context`; consider
optional `operationGuidance` separately. Neither can override CLI readiness,
the user's scope, or the frozen framework design. Confirm each task description
and checkbox still matches its returned source path and line.

Resolve original-design/wiki/rule conflicts before export. Select source IDs and
root-relative paths explicitly, including applicable source/rule files. Record
their hashes rather than treating a wiki summary as original authority. A store
outside the target module requires an explicit portable export, preserving source
identity; do not bypass path confinement or create a second planning system.

## Export and freeze

Keep the raw CLI response in local transient storage under the selected root;
it can contain machine paths and must not be committed. Supply a JSON mapping
of source IDs to relative paths. From the framework environment run:

```text
uv run python -m unity_coder.cli export-context --root <planning-root> --instructions <relative-apply-json> --sources <relative-source-map>
```

The output contains portable paths, hashes, schema identity and namespaced task
references. Save the output with the handoff. This is provenance, not evidence
that the contract covers every design requirement. The Architect must review
coverage and prepare computable shells, explicit bindings, placeholder art and
the presentation baseline before freezing the contract.

Runtime contracts belong at `specs/<feature>/contract.v<N>.json`, beside spec.md.
Map tasks using `<change>:<CLI-task-id>` and map tests explicitly to their author,
implementing units and criteria. Freeze tests before implementation; retain
contract bytes, protected inputs and baseline identities.

## Invoke and reconnect

The production Python entry point is `unity_coder.cli.invoke_local(boundary,
executor)`. The trusted host composes ProductionExecutor with a held RunLease,
the existing run BudgetLedger, and LocalExecutionServices. Local services bind
the module's WorkspaceManager/integration branch, configured ModelCodingWorkers,
the adapter's blocking verification ladder, target/presentation preflight and
ReviewGate. Do not expose callbacks, human authentication or run-state writes to
coders. A serialized graph request cannot select or construct these services.

The exported graph runs prepare, Red, parallel coding, sequential verification,
Refactor, final verification and review. Local invocation routes authenticated
acceptance to metadata-only completion, implementation findings to bounded
same-contract repair, and contract findings to a dossier. There is no standalone
`run` shell command that guesses deployment services; use the host-composed Python
entry point. The CLI export/status commands remain read-only with respect to
planning.

Read a current cycle with:

```text
uv run python -m unity_coder.cli status --root <planning-root> --instructions <relative-apply-json> --sources <relative-source-map> --contract <relative-contract> --state-root <external-state-root> --run-id <run-id> --adapter unity
```

Use the adapter's path-case policy. Prior contracts, when needed for validation,
are supplied with repeated `--previous` arguments in cycle order. Before invoking
a consecutive version, call `transition_cycle` with validated previous/current
contracts, new context, the same BudgetLedger, a held lease and a worker
reconciliation callback. It requires a completed rework result and matching
dossier, archives prior active records, and preserves progress sequence and token
reservations. Then construct the next ArchitectBoundary. Do not reset budgets or
change the run ID for rework.

Completed stage receipts are reused on reconnect. Missing receipts after external
effects stop for host reconciliation rather than replaying work. An operational
stop can resume explicitly through `resume_operational` only after the host has
reconciled effects and uncertain paid usage; retain unknown token reservations.

Progress is observation only. Operational/cancelled/abandon/rework are not passes.
Awaiting review requires a real human to inspect the exact candidate. Existing
contract bugs route to bounded repair; layout/design changes return to the
Architect for the next contract version. Never manufacture approval or substitute
model feedback for human identity. Accepted completion must descend from the
approved candidate and may only add accepted constraint metadata.

## Reconcile as Architect

Only accepted pass permits task reconciliation. `eligible_tasks` is advisory:
inspect accepted candidate, evidence and every mapped unit/criterion before
changing a checkbox. Unmapped or partially delivered tasks stay incomplete.
Rediscover OpenSpec task locations before editing them. The executor never writes
planning files. Continue specification verification, synchronization and archive
through the applicable OpenSpec workflows, preserving human gates.
