# Isolated artist replacement rehearsal

Set UNITY_HOST to the dedicated verification project and ART_REPLACEMENT_ROOT to
an external snapshot directory. Run with `uv run python
examples/visual_baseline/art_replacement.py <action>`.

The initial sequence is install, prepare, incompatible, compatible, export,
verify. The square delivery is rejected before asset mutation. The compatible
delivery replaces only PNG bytes and preserves its metadata, GUID, local sprite
ID and prefab binding. Frozen manifests reject those new bytes until a separate
manifest is prepared. No coder or active coding cycle receives these commands.

The actual reviewer requested a lake after reviewing the first compatible
candidate. Its receipt and evidence remain in the top-level art-replacement
evidence directory. Set ART_REPLACEMENT_REVISION=lake and use a distinct external
ART_REPLACEMENT_ROOT for the revised preparation, export and verification. The
helper must already be updated in the isolated editor tooling directory; refresh
and wait for the editor before issuing prepare, compatible, export and verify.
Never replay a mutation after receiving an uncertain reply: reconcile the
host's `.agent/art-replacement/` receipts first.

After an actual human decision, the trusted operator writes human-review.json
containing candidate_revision, decision, reviewer and the exact answer, then
runs accept only for decision=accept. This local receipt mechanism is a component
rehearsal, not production human authentication. Accept rechecks the candidate,
passing evidence and protected manifest files before invoking the replacement
policy. It does not complete a coding run or reset any budget.

The tests use only the six FrameworkVisualDemo selectors. The verification
request's profile and contract labels are rehearsal labels inherited from the
visual-review harness; the candidate hash identifies actual protected bytes and
all demo tests. The separate presentation manifest and import report record
the artist contract and imported identities. Artwork is synthetic geometric
fixture content, not final commissioned art.
