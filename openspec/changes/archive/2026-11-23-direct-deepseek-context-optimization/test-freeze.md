# Host-test preparation and freeze

Final closeout: 26 frozen test/fixture files, zero drift; **888 passed** in the
full suite (241.76 seconds), followed by **22 passed** after annotation-only
cleanup. Final isolated revision: `ac9416e998ee6ad022993350dc29aa0cc8236342`.
The last four tests first reproduced two author-note input failures and a real
committed-CRLF byte mismatch. Their fixes changed trusted helpers, not assertions.
Earlier counts below are historical checkpoints, not the final inventory.

49 new offline cases were run before helper implementation. They all failed
because the new modules do not yet exist. This is new-API absence evidence, not
Unity behavioral Red and not an assertion-only baseline; no game TDD claim is
made. The new host tests and twelve expected-source fixtures are now frozen by
`host-test-freeze.json`. During implementation the expected outcomes and test
bytes must remain unchanged. Additional checks can be appended in new files.

Coverage includes direct request dialect and actual/uncertain accounting;
explicit mixed role/effort policy; current-candidate/full-source identity;
conservative dependency closure; exact UTF-8 spans; forbidden notes and secrets;
malicious selector output and self-certification; unified optimized input/check
report; cache replay prevention; bounded Judge expansion; original verdict
preservation; unresolved references; and optimizer-inclusive cost.

The 199 existing lobby test/configuration files are separately frozen and intact.
The host fixture cases specify necessary evidence independently of model output;
they are not an adjudicated paid quality/routing pilot. Native valid Red and
Judge independence remain required for the actual lobby run.

Additional files were appended to the immutable inventory before their helpers:
live integration/feedback, recovery boundaries, retained Judge call limits,
genuine pilot receipt admission, metrics, paired corpus and rollout audit.
The latter five audit cases first failed with missing-module errors after the
pytest temporary-directory permission issue was removed; the focused audit and
existing integration set then passed 10 cases unchanged. These are host protocol
tests, not assertion-only game Red. Earlier implementation also exposed a literal
quoted-source preservation failure and the cumulative Judge claim reset defect;
both were repaired in helper code without editing the frozen tests.

After actual step9 discovery stopped before test submission, seven additional
exact-boundary Bridge recovery cases were authored and frozen before the helper.
All seven first failed on the absent module, then the seven plus existing
discovery/recovery checks passed 28 cases. No already frozen file was edited.

Final backend refinements append frozen tests for deterministic packing,
purpose-scoped qualification accounting, packing-version qualification, exact
archive hydration, nested direct usage and persistent routing. Initial direct/
mixed API shells left eleven failures including validation assertions before
implementation completed. Subsequent observed assertion failures included literal
quoted-source preservation, cumulative Judge claim accounting, packing overhead,
missing nested reasoning usage, absent rejected-call telemetry and stale prior
usage on unknown failure. Repairs changed helpers, never frozen assertions.
The initial 49-case missing-module baseline remains explicitly distinct from
these behavioral regressions and from the lobby's native assertion-only Red.

Final host inventory: 24 test/fixture files, zero hash drift. Latest complete
offline execution: **884 passed**, one existing collection warning, 259.57 seconds.
The corresponding isolated implementation checkpoint is `331b1d8`.
