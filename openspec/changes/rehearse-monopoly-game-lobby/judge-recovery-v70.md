# Cycle 70 Judge reconciliation

Candidate `be19106e61f8c5ce78cdde53803573616b9334fb` failed actual compilation:
`LobbyEconomy.cs(40,39): CS0103`, because `IgnoreSerializableAttribute` is used
as an undefined name. No tests ran. The subsequent Judge (GPT-6.1 Sol, medium)
call `v70-step5-verify-judge-ECON` failed operationally before a valid verdict.
Its durable failure is `{}`; a claim exists and an SDK completion receipt does
not. The original cause cannot be reconstructed from that evidence. Calling it
a proven TLS, timeout, model-cap or context failure would be speculation.

The complete **934,582 input / 32,768 output** reservation remains charged.
Accounting is **155,562,033 input / 6,471,507 output**, under unchanged
**250m / 24m / 160 cycles**. The original failed receipt, claim and pending
effect remain untouched. The recovery hook binds their exact hashes, confirms
the clean candidate and all 199 frozen files, registers this as the 26th retained
uncertain reservation, and uses public native operational resume. A fresh native
operation performs real verification and independent classification. No verdict
is fabricated and no failed paid call is replayed.

Caller-side diagnostic capture is added to the rehearsal composition. It records
whitelisted static error codes, hashes and approved model/effort metadata, then
rethrows the original error. It does not copy prompts, unknown error text or
diagnostic values. Successful replies and request arguments remain unchanged.
The framework's loss of the original static ModelError message is a separate
runtime observability defect; no framework runtime fix is included here.

The anchor transport also permits an actual model-authored unchanged-source
response when a complete current SHELL base needs no restoration and the current
compiler evidence implicates only peers. Restored bases still require concrete
edits, and blank reasons or changed bases are rejected. This avoids forcing
unrelated UI edits while ECON owns the current compile error. It does not claim
Green or skip shared verification.

Thirteen unchanged offline guards failed before implementation and subsequently
passed, alongside all six original anchor guards. Guard hashes:

- Peer no-op: `b9be5ef8076bad197cd3bf8137fe41bb253663477ea571c22acefd92cbfd170c`.
- Error capture: `7866a2112e027f890f73ac5b7af6a78d67895e1b98fb5df9688b05508633d48d`.
- Recovery: `4a095ec2ae480e3a780dbdb08ca3db8e8c439eeb70742e22abe2b1b982cd65f8`.

Full offline regression: **787 passed, one existing collection warning**.
The Architect/apply skills are
sufficient about retaining unknown usage, exact identity, frozen tests and
public resume. They do not supply this target-specific claim registration or
sanitized failure capture. Configured Coder, Judge, trusted overlay and framework
runtime remain unchanged. Not awaiting human review; no acceptance recorded.
