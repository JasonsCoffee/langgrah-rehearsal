# Separate framework performance finding

During cycle 68 Red, the run's progress journal reached **81,798,976 bytes**
(observed at 2026-11-21 02:03:44 UTC). The executor heartbeat uses a 0.25-second
wait between publications. Every `ProgressStore._publish` reads and validates
all prior JSONL records, appends one record in memory, serializes the entire
history and atomically replaces the complete journal. Status observation can
also reparse that full history.

This is an observed framework scalability defect: heartbeat work grows with the
whole retained run history, rather than the latest snapshot. It incurs repeated
CPU, allocation and filesystem traffic alongside the full host baseline scans.
The live process remained active with a current heartbeat. These observations
do not quantify how much of the total verification latency each activity causes;
no profiler or experimental runtime patch was applied to the pending run.

Relevant implementation: `src/unity_coder/core/progress.py` (`_records`,
`_publish`, `heartbeat`) and `src/unity_coder/core/executor.py` (`_observe`).

A separate framework change should preserve ordered history, atomic recovery,
sequence/contract validation and current status while avoiding full-history
reconstruction for each heartbeat. Do not truncate this run's journal or reset
its sequence as a workaround. The current lobby continuation changes neither
framework coordinator runtime nor the trusted overlay and continues the existing
sequential verification operation. This finding is not an unavailable capability
or evidence that the tests executed successfully.
