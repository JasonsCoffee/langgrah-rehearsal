# Provider migration evidence

Implementation checkpoint: isolated backend `cf09728`. Shared `src/`, original
tests, frozen lobby tests and pinned overlay sources are unchanged. The new host
composition uses the existing model-client interface and persistent ModelCalls.

The ignored local `ai.local.toml` selects direct `deepseek-flash`, low effort,
provider temperature, official HTTPS endpoint and a locally entered key. Its
previous bytes are backed up in ignored migration storage. No key is exported.
Requests send `thinking.type=enabled`, `reasoning_effort=low`, `max_tokens` and
JSON response format, with no tools, temperature or OpenRouter routing fields.
Normal TLS, direct connections and redirect refusal apply. Accepted returned
model names are an explicit Flash/version allowlist. Invalid identity, length,
JSON and reasoning-only replies are rejected while reported usage is retained.
Unknown submission keeps the entire reservation and stops rather than retries.

All Coder stages and format repairs share this direct client, superseding earlier
per-unit effort exceptions for future calls. Judge uses the existing Codex
app-server with GPT-6.1 Sol low and fresh independent, tool-disabled sessions.
Historical medium receipts remain historical; active low receipts require the
new matching authorization. The original cumulative 200-Judge-call guard counts
historical claims across policy epochs. It does not refill on effort change.

Output allocations remain 65,536 Coder, 32,768 Judge, 8,192 selector. Aggregate
limits remain 250,000,000 input / 24,000,000 output / 160 cycles / 2 added units.
No contract, run ID, old receipt or uncertain reservation is rewritten.

New helpers are `direct_deepseek_client.py`, `mixed_backend_policy.py` and
`mixed_backend_recovery.py` under the existing rehearsal host. Composition lives
in `lobby_production_host.py`; `actual_judge_feedback.py` validates active policy
and resolves the actual final expanded receipt. The mixed review path bypasses
legacy medium-effort review reuse; that historical helper is unchanged.

Offline request, ownership/anchor, receipt, recovery and historical-policy
regressions passed. Genuine direct and low-Judge pilot receipts also passed;
see `pilot-report.md`. Provider qualification is distinct from game acceptance.
