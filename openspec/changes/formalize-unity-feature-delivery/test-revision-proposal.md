# Proposed revision: Windows concurrent status readers

Status: adopted by explicit user approval on 2026-11-16. The original test and
freeze manifest are preserved under test-history/. Revision 2 adds the approved
bounded reader and explicit partial-JSON/persistent-error regression checks.

## Blocking evidence

Task 8.4 is blocked by
`tests/test_progress.py::test_status_is_always_complete_json_during_updates`.
The test opens status.json directly with Path.read_bytes while another thread
replaces it. On this Windows workstation, readers intermittently receive
PermissionError during replacement. No partial JSON was observed.

The fresh full suite reports 204 passed / 1 failed (8.29s, exit 1). The failing
test recorded 77 reader PermissionErrors. A separate disposable-file experiment
performed 100 replacements with each API:

| Writer API | Successful reads | Reader PermissionErrors | Partial JSON |
|---|---:|---:|---:|
| os.replace with bounded writer retry | 72507 | 554 | 0 |
| Windows ReplaceFileW with bounded writer retry | 2463 | 9945 | 0 |

The experiment uses only local temporary files and the standard library. These
observations establish the problem on this workstation; they do not claim every
Windows filesystem or every possible replacement API has identical behavior.

Writer-side transient rename errors are already handled with a two-second bound.
The remaining failure is reader-side. Rewriting in place would compromise the
atomic complete-snapshot requirement and is not proposed.

## Concrete proposed acceptance change

Revise only the concurrent reader portion of this frozen test under an explicitly
recorded new test revision. Preserve the original test hash/history. Readers may
retry PermissionError on Windows for at most two seconds. Every successful read
must still parse as complete JSON, writer exceptions still fail, all other reader
exceptions still fail, persistent access failure still fails, and the final
sequence must still equal 11. Do not skip the test on Windows.

The proposed reader operation is:

```python
def read_status(path):
    deadline = time.monotonic() + 2.0
    while True:
        try:
            return json.loads(path.read_bytes())
        except PermissionError:
            if os.name != "nt" or time.monotonic() >= deadline:
                raise
            time.sleep(0.001)
```

Use this operation in place of the unguarded read in the concurrent loop. Its
JSON decoder is outside the caught error class: partial JSON cannot be hidden by
retry. Document the same bounded-reader rule for clients of the file protocol,
then freeze the revised test and rerun the targeted and full suites.

The user approved this test revision and continuation. No other frozen test is
authorized to change. Task 8.4 completion still requires fresh passing evidence.
