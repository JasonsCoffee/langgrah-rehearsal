# Isolated visual baseline

Architect preparation for task 10.3. This synthetic expedition screen does not
implement a Monopoly feature. Existing game files and tests are not edited.
All generated content lives in new FrameworkVisualDemo folders on the dedicated
host; the external preparation worktree retains the identical frozen bytes.

## Review

Open the dedicated host's scene:
`Assets/JJGame/monopoly/Runtime/Resource/monopoly/Scenes/FrameworkVisualDemo/VisualBaseline.unity`.
Use a portrait Game view (design resolution 1080 x 2160), enter Play Mode, and
inspect the title, illustration, destination, metrics, status and buttons.
The primary button changes the status to READY FOR REVIEW in mint; Reset preview
restores BASELINE PREVIEW in coral. Exit Play Mode after reviewing. These are
presentation preview controls, not a game implementation or automated PlayMode test.

Review spacing, contrast, readability, image crop and button size against
[the synthetic brief](design.md). Approve `visual-baseline-v1` with the manifest
identity in the evidence review.json, or describe changes. Preparation completion
does not approve the baseline or authorize a coding cycle.

## Preparation and reproducibility

Set `UNITY_HOST`, `UNITY_BRIDGE_PORT` and `VISUAL_BASELINE_ROOT` locally. The last
must select an isolated game-repository worktree outside Unity's Assets tree.
The active dedicated editor needs the existing game-local FrameworkVerify helper.
No package installation or modification of shared source is performed here.

```text
uv run python examples/visual_baseline/live.py install-tests
uv run python examples/visual_baseline/live.py red
uv run python examples/visual_baseline/live.py install
uv run python examples/visual_baseline/live.py create
uv run python examples/visual_baseline/live.py green
uv run python examples/visual_baseline/export.py
uv run python examples/visual_baseline/live.py open
uv run python examples/visual_baseline/live.py check-originals
```

`create` refuses to overwrite existing scene, prefab or artwork. `inspect` exports
fresh evidence without regenerating the baseline. Install refuses conflicting
existing source bytes. Explicit revisions require a new reviewed preparation.
This helper is an Architect-side fixture, never an executor/coder operation.

The builder reuses native Unity prefab/scene/import APIs and the installed
`PsdPrefabLayoutAutomation.InspectPrefabLayout` read-only inspector. The synthetic
reference has no PSD or game map, so PSD conversion and map generation are not
invoked. Existing PSD sources, map assets, bindings and original Docs~ remain intact.
For actual PSD-based features retain the target's existing conversion pipeline,
then inspect its resulting prefab rather than recreating shared infrastructure.

The report contains actual hierarchy, serialized component bindings, persistent
button listeners, import properties, canonical GUIDs, encoded metadata identities,
content hashes, scene-load and missing-script checks. Export uses the existing
Unity signature validator and generic Presentation distribution. Artist requirements
cover dimensions, transparency, variants, import settings, usage and replacement
acceptance. Replacement is a separate change after review.

Evidence lives in the active change's `live-evidence/visual-baseline/`. Manual
screenshots show the initial and ready states. The fixture does not claim real
game feature acceptance, mobile safe-area coverage, final art or task 12.4/12.5.

## Human-review rehearsal (12.4)

The user approved mint v1, requested a warm-coral primary button, then explicitly
approved v2 and its interactions. The original files remain in the external v1
preparation worktree. V2 uses the same scene path; its evidence and acceptance
are in `live-evidence/visual-review/`. Artist replacement remains a separate task.

`review_rehearsal.py` exercises the real ReviewGate, RunLifecycle and BudgetLedger
with live Unity compile/EditMode results. It is trusted operator tooling, not a
coder tool, production authenticator, or new exported-graph/model execution.
Fixture contract identifiers are rehearsal labels, not claimed full production
contract exports. The prior production run and its accounting are untouched.

The supervised diagnostic injects a ready-handler text defect outside a coding
cycle, proves that prior approval cannot accept changed source, then restores
the implementation byte-for-byte. The new interaction tests enable runtime
listeners only on temporary prefab instances; authored bindings are unchanged.
The color test is Red before the Architect's presentation revision and Green
afterward. Both revisions retain one rehearsal ledger, with no model calls.

Set VISUAL_REVIEW_ROOT to external operational storage. Only the trusted operator
may import actual chat decisions as human-baseline-approval.json,
human-presentation-request.json, or human-v2-approval.json. Never manufacture a
receipt from an agent's assessment. accept-v2 checks the exact pending candidate
identity and current bytes before recording the human's decision. The accepted
review does not itself perform metadata completion, merge or push.
