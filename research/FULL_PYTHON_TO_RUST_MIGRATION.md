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

## Next dependency-aware work

1. Finish and independently verify the CI policy subset, then assess the
   rest of its Python-only formatting/orchestration surface.
2. Prioritize reproducible, side-effect-free verification/reporting helpers
   with explicit semantics, adding Rust-native tests and Python differential
   controls before switching defaults.
3. Tackle remaining 58 core modules and 76 parallel/14 partial ones based on
   runtime dependency and soundness risk rather than filename count alone.
4. Track CLI, benchmark scripts and tests separately; preserve independent
   checkers where they are required for certification.

No new claim of full migration or a general SAT complexity theorem is made.
