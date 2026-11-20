# Prepared fake-match randomness input

LobbyWorld now declares the nonfunctional, instance-owned `System.Random
SeatAllocationRandom` field requested by the actual Queue dossier. The fake match
service must use the supplied source to allocate solo participants among remaining
seats while preserving full parties, faction labels and unique membership. Null
uses its normal fake-server randomness. This declaration supplies no allocator or
business implementation; those remain delegated to MATCH.

Both fixtures in any reproducibility comparison must supply controlled inputs.
Different seeds can legitimately collide; never require every pair of different
seeds to produce different assignments. Prove the source is actually consulted
and that controlled random choices influence legal allocation. An independently
authored recording/scripted System.Random subclass is a valid input fixture, but
must not manufacture match results or allocate seats itself. Assert reproducible
same-input behavior and preserved seat/party constraints. Do not use reflection
to demand an undeclared seam or call missing APIs as behavioral Red. Update the
clause maps to describe actual observed assertions.
