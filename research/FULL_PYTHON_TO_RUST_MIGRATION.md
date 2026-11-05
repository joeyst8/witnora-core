# Witnora full Python→Rust transfer: source-file execution ledger

The user requested completion of the remaining Python→Rust migration after the
R-500 research gate. A **milestone number is not a migrated Python file**.
Never declare the whole transfer complete based on a test counter.

Source-file inventory at the R-500 baseline:

| Group | Not migrated | Parallel Rust reference | Partial native verified | Total |
|---|---:|---:|---:|---:|
| `witnora_core` | 58 | 76 | 14 | 148 |
| `scripts` | 117 | 0 | 0 | 117 |
| `tests` | 295 | 0 | 0 | 295 |
| **All** | **470** | **76** | **14** | **560** |

## Source-file migration rules

1. Preserve each Python source file and independent proof verifier until its
   Rust replacement is compiled, behaviorally compared on normal and hostile
   cases, and all relevant GitHub CI passes.
2. Record a Rust implementation of a **subset** of a Python module as
   `parallel_reference` at most; do not mark it fully transferred.
3. Native-default or full-native designations require an explicit public API
   parity inventory, successful differential tests, and a verified choice of
   trust boundary and fallback behavior. This is not achieved by adding one
   Rust function to a large Python module.
4. Keep Python/Lean/independent external `drat-trim` verification separate
   during the migration; switching exporters must never imply source-CNF
   verification or SAT/UNSAT certification by itself.
5. `scripts` (117) and `tests` (295) are individually reviewed: some should
   remain independent Python interoperability checks; rewriting them
   wholesale can destroy the independent regression oracle.
6. Keep all work on draft PR #122. Do not merge until release criteria pass.

## Migration wave 1: CI failure-policy decision kernel

Source: `witnora_core/ci.py` (`not_migrated` at R-500 baseline).
Rust candidate: `rust/witnora-ve/src/ci_fail_policy.rs`.
New opt-in functions: `ci_failure_reasons_native`,
`ci_marketplace_failure_reasons_native`.

The Python `evaluate_fail_conditions` and
`evaluate_marketplace_fail_conditions` remain default and independently
tested. Both expose an explicitly opt-in `backend="rust"` mode for the
decision subset. Seeded differential tests exercise 1,024 policy inputs,
in addition to control cases and native Rust unit tests. This is **not** a
full transfer of `ci.py`; its CLI, report writing, trust-card formatting and
GitHub workflow integration still execute in Python.

Wave 1 status: **parallel Rust reference verified** by focused CI
[#41965400103](https://github.com/joeyst8/witnora-core/actions/runs/41965400103)
and full Rust CI
[#41965400113](https://github.com/joeyst8/witnora-core/actions/runs/41965400113).
The manifest now records 469 not migrated, 77 parallel Rust references, and
14 partial native verified. **Zero full-module conversions are claimed**.

## Migration wave 2: deterministic benchmark Markdown renderer

Source: `witnora_core/report.py` (`not_migrated` at R-500 baseline).
Candidate: `rust/witnora-ve/src/benchmark_report.rs`, with JSON decoding and
full Rust construction of the benchmark overview, counts, route tables,
reduction statistics, determinism, no-collapse and width-skip sections, and
explicit claim boundaries.

`generate_markdown_report(..., backend="rust")` is opt-in; the unmodified
Python renderer remains the default and byte-for-byte oracle. Normal,
adversarial missing-field and 128 seeded report fixtures run through native
differential tests in focused CI. The file still contains a Python CLI and
is **not** a complete source-file migration.

Wave 2 status: **parallel Rust reference verified** by focused CI
[#41966761084](https://github.com/joeyst8/witnora-core/actions/runs/41966761084)
and full Rust CI
[#41966761079](https://github.com/joeyst8/witnora-core/actions/runs/41966761079).
Current manifest counts: 468 not migrated, 78 parallel, 14 partially native
verified; still **zero fully migrated source files**.

### Native executable completion gate (verified)

`rust/witnora-ve/src/bin/witnora_report.rs` now provides an entirely
standalone Rust command-line program: `witnora_report BENCHMARK_JSON --out
REPORT_MD`. It requires no Python runtime and uses the native Markdown
renderer. The focused CI builds the executable and compares its output bytes
against the original Python report CLI over empty, nontrivial and seeded
instances. Malformed and missing input fail without creating a report.
The Rust executable also accepts the output flag on either side of the input
and supports a standalone help command. The end-to-end, no-Python executable
gate passed focused CI
[#41968925434](https://github.com/joeyst8/witnora-core/actions/runs/41968925434)
and full Rust CI
[#41968925507](https://github.com/joeyst8/witnora-core/actions/runs/41968925507).

This checks the **entire report-generation CLI operation** in Rust, but the
original Python import/API remains available for independent comparison and
compatibility. Its source-file manifest status remains `parallel_reference`:
the executable gate is satisfied, but a native-default deployment and
replacement policy (including packaging, all public entry points, fallback
rules, and independent acceptance) is still outstanding. A successful native
CLI is **not** a claim that 560 Python files have been transferred.

## Migration wave 3: standalone native benchmark comparison

Source: `witnora_core/compare.py` (unmigrated at the R-500 baseline).
Native candidate: `rust/witnora-ve/src/benchmark_compare.rs` with its
no-Python `witnora_compare LEFT_JSON RIGHT_JSON --out COMPARISON_MD` CLI.
The original Python comparator remains the reference for output ordering,
route/status changes, delta arithmetic, missing fields and determinism tables.
The focused differential gate passed 128 seeded paired benchmarks, empty
inputs, nontrivial changes, help, output-argument ordering and malformed JSON.
The standalone CLI passed focused CI
[#41969969453](https://github.com/joeyst8/witnora-core/actions/runs/41969969453)
and full Rust CI
[#41969969583](https://github.com/joeyst8/witnora-core/actions/runs/41969969583).
This is a verified Rust executable, **not** a complete source-file migration:
the Python module/CLI remains the default and a packaging/default/replacement
policy has not passed. The ledger records it as `parallel_reference`.

After wave 3, the tracked Python source-file statuses are 467 not migrated,
79 parallel Rust references and 14 partial-native verified, for 560 total.
No fully native-default source module is claimed.

## Next dependency-aware work

1. Finish and independently verify the remaining CI CLI/report orchestration,
   which still has Python-only code despite the verified policy subset.
2. Prioritize reproducible, side-effect-free verification/reporting helpers
   with explicit semantics, adding Rust-native tests and Python differential
   controls before switching defaults.
3. Tackle the remaining 55 unmigrated core modules, and review the 79 parallel
   and 14 partial modules based on runtime dependency and soundness risk rather
   than filename count alone.
4. Track CLI, benchmark scripts and tests separately; preserve independent
   checkers where they are required for certification.

No new claim of full migration or a general SAT complexity theorem is made.
