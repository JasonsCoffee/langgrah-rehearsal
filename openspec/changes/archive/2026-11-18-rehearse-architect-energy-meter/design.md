# Design

## Context

This is a live rehearsal of the delivered Unity adapter and production graph. The framework design remains authoritative.

## Goals / Non-Goals

Use two Editor-only assemblies for pure operations and their EditMode fixture. The review covers code and selected test evidence.

## Decisions

Unit spend owns `Editor/Script/FrameworkArchitectDemo/Code/EnergySpend.cs` and unit recharge owns `Editor/Script/FrameworkArchitectDemo/Code/EnergyRecharge.cs`. Each exposes an instance method Apply(int current, int capacity, int amount). Their dependency is shared acceptance through the returned integer. Unit tests owns `Editor/Script/FrameworkArchitectDemo/Tests/EnergyAcceptance.cs`. The independent judge reviews test preparation before live Red and global freeze.

Use dedicated trusted composition through invoke_local, with a persistent budget, held lease, confined materialization and blocking Bridge verification. Use empty presentation data for code-only review.

## Risks / Trade-offs

Integer overflow is covered by the maximum-request recharge case. Explicit test IDs and a candidate identity check constrain verification. Existing target files are outside the candidate scope.
