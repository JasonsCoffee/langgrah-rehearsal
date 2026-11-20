# Brainstorm

## Outcome and acceptance criteria

Exercise the delivered Architect-to-LangGraph path with two cooperating Editor-only C# units. From 7 of 10, spending 3 then recharging 8 yields 10.

## Current evidence and constraints

The dedicated Bridge reports protocol 1, compile and tests, and a ready editor. Both the isolated root and the diagnostic mount were unused at inspection. The boundary, verification, adapter and retry specifications govern this rehearsal.

## Alternatives and trade-offs

Two pure operations connected by an acceptance test exercise shared verification with no scene or gameplay dependency.

## Decisions and assumptions

Use signed 32-bit integers. A valid state satisfies capacity >= 0 and 0 <= current <= capacity. Reject invalid state before processing any amount, using ArgumentOutOfRangeException for capacity first, then current. Zero capacity is valid. Negative and zero amounts preserve valid current. Recharge saturates without overflow.
