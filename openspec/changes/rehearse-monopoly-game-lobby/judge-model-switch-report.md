# Judge model amendment

The user explicitly requested `glm-5.3-flash`. Only the judge's model assignment
in local configuration changed from `openai/gpt-6-astra` to
`z-ai/glm-5.3-flash`. The coder remains `deepseek/deepseek-v4.1-flash`, pinned to
Alibaba. Credentials, endpoints, configured reasoning/temperature policies,
candidate, trusted overlay, frozen-test rules and independent judge separation
were preserved. No framework runtime file changed.

The change was made at the completed cycle-23 rework boundary, with no worker
in flight. Retained candidate: `1f549a005cae6ed1e7501b379f4d42121b2add0c`.
The first real GLM response correctly rejected a deliberately vacuous assertion,
but surrounded its JSON with Markdown fences. Its 104 input / 124 output tokens
remain charged. The framework's strict parser was not relaxed.

Target-only transport now requests OpenRouter `json_object` response mode for
this exact judge model. Explicit stronger formats and every other model/role
remain untouched. Five offline checks were Red before implementation and frozen
at SHA-256 `5703d75284909f8ef231a26726793e6254ab95e198c61a29bcf255d9b2f43f18`.

Live JSON-mode validation is **blocked**, not passed. Both the initial check and
its single new-call retry failed to connect. A non-billable metadata request
confirmed `SSLEOFError: UNEXPECTED_EOF_WHILE_READING` against OpenRouter. No further
paid retries or model substitutions occurred. Both uncertain reservations remain
intact; exact receipt hashes and reservations are bound in trusted operator
evidence and recognized by the next transition/recovery reconciliation callback.
Five new reservation checks were Red then frozen at SHA-256
`55add9ee28d8437e418a5f2cf6c031062e4693e0ed30bd3d9aea80f0494974ba`.
All fifty offline rehearsal wiring checks pass. These are not selected Unity tests.

Accounting after this work is 16,019,923 input / 2,491,086 output, including every
previous charge and four uncertain reservations. Active limits remain 18,000,000 /
5,400,000 and thirty cycles. The explicit 24,000,000 / 7,200,000 authorization is
pending its supported native recovery boundary; it has not silently changed the
active ledger. Live source review can resume when OpenRouter connectivity is
restored. No global test freeze, feature implementation dispatch, selected lobby
EditMode execution, human-review offer or acceptance is claimed.

The skill's configured-model independence and explicit reconciliation rules were
sufficient. Target JSON-mode request wiring and non-mutating calibration receipt
reconciliation had to be supplied locally. The network failure is an external
execution blocker. Public evidence: `evidence/judge-model-switch-glm-v23.json`.
