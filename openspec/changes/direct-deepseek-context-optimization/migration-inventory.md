# Migration inventory

The existing run is operationally stopped at candidate
`625db77bf4e75060435947d955328a729f6f87dc`, contract version 70, with completed
verification transaction `v70-step8-verify`. Accounting is 160,700,047 input /
6,517,038 output, including 27 unresolved reservations. Limits remain
250,000,000 / 24,000,000 / 160 cycles / 2 added units.

The isolated backend is clean and saved at `b322e2c`; the planning checkpoint is
`772b2d8`. Exact call-set, old file and frozen inventories are hashed in
`migration-inventory.json`; the private full ledger snapshot is under
`.agent/direct-deepseek-migration/before.json` in the planning checkout.
All 199 frozen files match. Both pinned overlay source hashes and the recorded
81,134-file baseline identity match their original values; the full physical host
scan passed before the paid pilot. No run-owned Python process was
active; two historical unrelated Python processes are preserved.

The latest unknown Judge call is `v70-step8-verify-judge-ECON`, reserved
2,694,310 / 32,768, failure `{}`, receipt hash
`60b94160bfa531463581eccb61fc3a7d70f53f6388d898346da72c3ba09f6391`.
It requires registration alongside all prior unknown calls; no refund or replay.
Native resume must use new operation and role-policy identities, and preserve
its completed verification and pending Judge effect unchanged. The retained
caller trace identifies `incomplete_turn`; the native failure object alone is
empty and establishes no transport or billing cause.

The user refined secret storage to the existing ignored `ai.local.toml`.
The old configuration is backed up locally; no credential is copied into tracked
profiles, packets, logs or model messages. The user populated the local key and
authenticated model-list and paid protocol checks passed. The host implementation
checkpoint is `cf09728`. The paid pilot added 96,035 input / 1,028 output, with
all historical call records unchanged; see `pilot-report.md`. Native activation
remains separately recorded rather than inferred from pilot success.
