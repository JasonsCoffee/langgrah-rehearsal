# Presentation Baseline Spec Delta

## Purpose

Make prepared Unity presentation assets a reproducible input to coding and a
reviewable delivery contract for replacement artwork supplied by artists.

## ADDED Requirements

### Requirement: Architect prepares a usable presentation baseline
Before contract freeze the Architect SHALL prepare placeholder art, imported assets, scenes/prefabs, compilable component shells, explicit bindings, and launch/review instructions for the planned experience. The coding contract SHALL reference the actual baseline rather than an inferred future hierarchy.

#### Scenario: Interactive screen enters execution
- **WHEN** a feature includes a designed screen with artwork and interactions
- **THEN** the baseline contains its layout, placeholder assets, component shells, and declared bindings before implementation units dispatch

### Requirement: Baseline is validated and identified
The baseline SHALL identify content hashes, asset identities, scene/prefab structure, import settings, serialized component interfaces, and review references. Preflight SHALL reject missing scripts, unresolved required references, incompatible shells, or an unlaunchable review scene before coding begins.

#### Scenario: Shell exists but binding is missing
- **WHEN** a required button binding points to a missing component or member
- **THEN** baseline preflight fails and the Architect repairs preparation before freeze

### Requirement: Frozen presentation integrity
The executor SHALL prohibit changes to frozen artwork, layouts, scene/prefab structure, import settings, and serialized binding interfaces throughout a contract cycle. Integrity enforcement SHALL cover protected asset identities independently of generated-file ownership exemptions.

#### Scenario: Patch alters a frozen scene
- **WHEN** an implementation patch changes a frozen layout or prefab hierarchy
- **THEN** integration rejects the patch before verification

#### Scenario: Identity changes through a sidecar
- **WHEN** an existing protected asset's metadata changes its GUID or import settings
- **THEN** integrity validation rejects the change even if that file is exempt from ordinary ownership checks

#### Scenario: Script edit breaks serialization
- **WHEN** an owned script renames a frozen serialized field or changes a required component identity
- **THEN** conformance rejects the incompatible edit without requiring a scene-file diff

### Requirement: Runtime behavior respects the binding contract
Implementation units SHALL implement declared runtime behavior through prepared bindings without modifying the authored baseline. Runtime text, visibility, selection, animation, and instantiation SHALL be permitted only as described by the feature contract.

#### Scenario: Runtime state updates a prepared view
- **WHEN** gameplay changes the displayed score through a declared binding
- **THEN** the update is allowed without being treated as an authored layout modification

#### Scenario: Implementation needs another serialized component
- **WHEN** behavior cannot be implemented using the frozen component interface
- **THEN** the unit reports a contract defect rather than editing the prefab or adding an undeclared binding

### Requirement: Placeholder assets define final-art delivery requirements
Each replaceable asset SHALL have a stable ID, purpose, visual reference, dimensions/aspect ratio, transparency requirements, variants, applicable import settings, usage references, and replacement acceptance criteria. Placeholder polish SHALL NOT be required for functional human acceptance.

#### Scenario: Artist receives a placeholder specification
- **WHEN** final artwork is commissioned for a prepared UI asset
- **THEN** its manifest provides the delivery and import requirements needed to replace it without rewriting behavior or rebuilding layout

### Requirement: Final-art replacement is a controlled later change
Final artwork SHALL replace placeholders through a separate Architect-controlled change that validates asset compatibility, preserves required references, and repeats visual review. Replacement SHALL NOT occur inside a frozen coding cycle.

#### Scenario: Replacement changes slicing or typography
- **WHEN** final art requires incompatible borders, font metrics, or import settings
- **THEN** the replacement change revises the affected presentation contract and obtains renewed review instead of silently accepting the substitution

### Requirement: Presentation behavior remains adapter-specific
The core SHALL handle generic immutable input manifests and integrity evidence. Unity scene serialization, GUIDs, component checks, import validation, and editor-based preparation SHALL remain behind Unity-specific tooling or adapter boundaries.

#### Scenario: Framework tests run without Unity
- **WHEN** presentation protection is exercised in the framework test suite
- **THEN** fake manifests and adapter evidence verify enforcement without importing Unity tooling or contacting a model

### Requirement: Prepared art belongs to the game baseline
The Architect SHALL prepare presentation changes in an isolated game-repository checkout, reuse compatible existing content/tools, and record one immutable baseline revision. Assets SHALL follow the target's resource, bundle, placeholder naming, and identity conventions. Coding workspaces and verification SHALL consume that same baseline.

#### Scenario: Existing scene already provides required structure
- **WHEN** a feature extends an existing game scene with compatible bindings
- **THEN** preparation reuses that scene and adds only required feature content instead of rebuilding shared project infrastructure

#### Scenario: Baseline reaches isolated workspaces
- **WHEN** the frozen game baseline is distributed to coding units and the verification host
- **THEN** each copy preserves the same asset content and tracked metadata, while original design sources remain unchanged
