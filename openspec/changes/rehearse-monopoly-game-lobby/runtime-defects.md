# Separate runtime follow-up

During version twelve, the configured coder returned a complete-looking patch
with raw newlines and unescaped C# quotation marks inside JSON string values.
The paid response and its exact provider usage were durably recorded.
`ModelCodingWorkers.code` passed it to `parse_patch`, which raised `ValueError`.
That exception escaped the native graph, leaving the prepare operation pending
and its worker effect without a result. It did not produce a normal operational
result that could use `resume_operational`.

This needs a separately scoped decision about malformed-output classification
and owner reconciliation. A runtime fix must preserve the original paid receipt,
retain accounting, prevent automatic replay, preserve frozen tests, and require
normal ownership validation and independent review for any recovered patch.
The current rehearsal did not modify runtime error handling.

Trusted target wiring instead made one new, explicitly identified formatting-only
call to the configured coder. It supplied the actual malformed response, required
strict JSON, and validated the returned full files against the original unit's
ownership. Only that actual delegated result resolved the exact pending worker
effect. The original receipt and charge were preserved, and the native prepare
operation continued to the independent judge. The audit intent and completion
records live under `recovery-authorizations/v12-json-format-*.json` in trusted
state. No judge verdict or human approval was fabricated.
