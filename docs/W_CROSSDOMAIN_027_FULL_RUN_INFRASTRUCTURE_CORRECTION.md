# W027 full-run infrastructure correction (no benchmark retuning)

The first full W027 GitHub Actions execution
([run 42139971305](https://github.com/joeyst8/witnora-core/actions/runs/42139971305),
commit `66f3172286adbde403f1e7d1fd4934a1299c5aab`)
passed Rust, independent harness, Kissat, and CryptoMiniSat build/check
steps. It then exhausted its **27-minute workflow step allowance** at
2026-11-06 01:22:24 UTC, after reporting completed cases 1–199 of 204.
Its final JSON was never written; it is **not a completed study**.
This is an infrastructure budget failure, not a solver verdict or
mathematical counterexample. The original log preserves the first
199 per-case verdict summaries and the explicit timeout message.

The corrective rerun changes **only**:

1. Overall GitHub job allowance: 40 to 60 minutes; full benchmark
   workflow step allowance: 27 to 48 minutes.
2. Stream a source-hash-pinned, per-invocation JSONL checkpoint to disk
   **after** each full case completes, outside its measured arm runtimes.
   GitHub uploads it even if the workflow is interrupted.

The frozen 204 case IDs, all 96 W026 matched pairs, all eight W022
external inputs and hashes, four decoy hashes, source solver commits,
three-arm order rotation, three repetitions, 30-second **per invocation**
cap, 2 GiB memory cap, and correctness checks remain unchanged.

Do not pool partial pilot timings with the new rerun or claim a
successful full result before the new job passes. Reporting includes
the failed first attempt for audit transparency.
