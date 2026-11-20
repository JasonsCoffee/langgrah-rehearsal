# Explicit catalog integration disposition

The user was asked whether US-L7-11's production Luban registration and AssetGraph
packaging should be included, or whether the prepared game-owned catalog should
stand in for that data/build integration. The exact response was:
"Use rehearsal catalog; defer production integration".

For this rehearsal, use the existing game-owned ScriptableObject catalog and
imported placeholder assets. US-L7-11 still requires complete skin and vehicle
fields, exact configured products/prices, and one shared catalog data source for
Appearance and Shop. Verify both catalog kinds and effective data provenance;
matching IDs alone does not prove shared provenance.

Production Luban table registration, generation and AssetGraph packaging are
explicitly deferred and must be reported as a delivery limitation. Do not claim
that an Editor import or a keyword search proves production packaging. Do not
execute generation/publish scripts or mutate the original registry/graph files.

This is a scope decision, not candidate approval. All other functional
requirements, the prior handoff disposition, frozen-test ordering and independent
review remain unchanged. The qualitative visual allocation in
verification-strategy.v16.md remains bound to pending human review of the exact
candidate under framework D-26.
