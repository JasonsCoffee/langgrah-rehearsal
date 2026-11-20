# architect-energy-diagnostic Specification

## Purpose

Exercise independent coding ownership and shared acceptance in an Editor-only arithmetic diagnostic.

## Requirements

### Requirement: Spend energy

The spending operation SHALL reduce valid current energy by a positive request, saturating at zero. Nonpositive requests SHALL preserve current.

#### Scenario: Spending bounds

- **WHEN** current is 7 of 10 and the request is 3, 8 or -3
- **THEN** the respective result is 4, 0 or 7

### Requirement: Recharge energy

The recharging operation SHALL increase valid current energy by a positive request, saturating at capacity without integer overflow. Nonpositive requests SHALL preserve current.

#### Scenario: Recharging bounds

- **WHEN** current is 7 of 10 and the request is 2, int.MaxValue or -3
- **THEN** the respective result is 9, 10 or 7

### Requirement: Valid state and composition

Both operations SHALL accept integer state with nonnegative capacity and current between zero and capacity inclusive. Both SHALL reject invalid state with ArgumentOutOfRangeException, checking capacity before current and state before amount.

#### Scenario: Shared acceptance

- **WHEN** a caller starts with 7 of 10, spends 3, and recharges 8 using the spending result
- **THEN** the intermediate current is 4 and final current is 10

#### Scenario: Invalid or empty state

- **WHEN** capacity is negative, current is negative, or current exceeds capacity
- **THEN** both operations reject the state
- **WHEN** capacity and current are zero
- **THEN** both operations return zero for a positive request
