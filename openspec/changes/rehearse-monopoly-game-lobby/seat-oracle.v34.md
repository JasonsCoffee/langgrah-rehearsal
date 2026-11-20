# Deterministic fake allocation contract

The actual cycle-33 dossier exposed an underspecified random-allocation oracle.
For this rehearsal, the fake match allocator uses this explicit selection rule.
Full two-member parties receive intact factions before solo allocation. Each
seat has its existing stable index in the match's 24-seat list. The available
solo pool is the ascending list of seat indices not occupied by full parties.
Process real solo accounts in ordinal account-ID order. For each, call the
instance's SeatAllocationRandom.Next(currentPool.Count), take that pool position,
assign the account there, then remove that position. Fill the remaining positions
with fake bots. A null input uses normal fake-server randomness following the
same selection rule. Do not randomize the already assigned party seats through
this solo input. These are fake-service design rules; MATCH implements them.

The test author must independently compute expected controlled picks from the
known seat-index pool, never copy an implementation-produced assignment as its
oracle. Controlled lowest-index choices and highest-index choices from pools
with multiple remaining positions have independently known results. A fixed
allocator that merely calls and discards the source cannot satisfy both. Assert
all relevant legal-seat and party invariants for each run. Same-seed runs must
install sources before any allocation; arbitrary different seeds may collide.
No handwritten test or allocator implementation is supplied by the Architect.

This rule resolves the rehearsal's internal algorithm choice without waiving
random allocation, changing seats/fees/faction requirements or adding gameplay.
It supersedes only the earlier unspecified solo-selection mechanics. Keep all
other source clauses, atomic-start assertions and financial ownership coverage.
