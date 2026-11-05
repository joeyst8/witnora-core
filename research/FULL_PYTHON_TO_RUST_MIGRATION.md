# Witnora full Python→Rust transfer: source-file execution ledger

The user requested completion of the remaining Python→Rust migration after the
R-500 research gate. A **milestone number is not a migrated Python file**.
Never declare the whole transfer complete based on a test counter.

## Research direction decision — selective Rust acceleration (2026-11-05)

The owner has superseded the earlier objective of converting every Python file.
**The 560-file count is a historical inventory, not a release target or a
measure of Witnora's scientific progress.** Keep the ledger for provenance
and compatibility audits, but do not pursue 100% Rust conversion by default.

Witnora will use a hybrid architecture:

- **Rust:** performance-critical, deterministic solver kernels and data
  structures when profiling or benchmarks justify a port.
- **Python:** experimentation, automation, high-level orchestration,
  benchmarking and independent cross-language reference behavior.
- **Lean:** formal proofs and source-bound theorem checking.
- **Independent checkers:** DRAT and other external evidence verification;
  the producer must not become its sole proof authority.

Prioritize TC-063 and W-CRC research, with measured solver performance and
correctness as the outcomes. For each proposed Rust port, record (1) a
profiled bottleneck or clear integration need, (2) an exact behavioral and
resource-limit contract, (3) adversarial Python/Rust differential tests,
(4) independent proof/source-checker gates when applicable, and (5) a
reproducible benchmark including comparison with established external
solvers. Retain the Python path if Rust brings no material benefit.
Native-default adoption remains a separate review and release decision.

Do not remove the existing Python tests, research scripts, or Lean/external
verification gates merely to increase a migration percentage. No prior
native-verification claim is strengthened by this policy change.

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

## Migration wave 4: standalone claim-boundary file scanner (verified)

Source: `witnora_core/claim_boundary.py` (already `parallel_reference` from
R-080). Its existing Rust text scanner is now exposed through the standalone
`witnora_claims FILE [FILE ...] [--out RESULTS_JSON]` command, including
file-level findings, forbidden-claim aggregation and fail-closed invalid-file
handling. The focused gate compares the complete multi-file JSON result with
the independent Python API across 128 seeded Unicode-adjacent files and
normal/adversarial controls. Focused CI
[#41971663155](https://github.com/joeyst8/witnora-core/actions/runs/41971663155)
and full Rust CI
[#41971663031](https://github.com/joeyst8/witnora-core/actions/runs/41971663031)
passed. This executable path is verified, but the original Python API is
still the default; the manifest category remains `parallel_reference`.

## Migration wave 5: strict benchmark artifact UNSAT summary (verified subset)

Source: `witnora_core/benchmark_artifact.py` (`not_migrated` before wave 5).
Candidate Rust implementation: `rust/witnora-ve/src/benchmark_artifact_summary.rs`,
with Python-free `witnora_artifact_summary BENCHMARK_JSON [--out SUMMARY_JSON]`.
Only the `strict_verification_summary` pure-data function is reproduced;
artifact packaging, certificate copying, report composition and archive
creation remain Python. The opt-in CLI is compared with Python on 128 seeded
benchmark records, including every UNSAT evidence category, and rejects
malformed JSON without creating an output. The critical rule is unchanged:
native XOR UNSAT labels never count as independently `drat-trim`-certified.
Focused CI
[#41971995324](https://github.com/joeyst8/witnora-core/actions/runs/41971995324)
and full Rust CI
[#41971995371](https://github.com/joeyst8/witnora-core/actions/runs/41971995371)
passed. The ledger now records this **verified subset** as `parallel_reference`,
not as a full source-file replacement.

After wave 5, the tracked source-file statuses are 466 not migrated, 80
parallel Rust references and 14 partial-native verified, for 560 total.
The current research branch has four Python-free reporting/scanning binaries:
`witnora_report`, `witnora_compare`, `witnora_claims`, and
`witnora_artifact_summary`. None should be mistaken for a native-default
replacement of the original Python module.

## Migration wave 6: native CI log-summary renderer (verified subset)

Source: `witnora_core/ci.py` (already `parallel_reference` from wave 1).
The Python-free `witnora_ci_summary REPORT_JSON FAILURE_REASONS_JSON
[--out SUMMARY_TXT]` executable renders the complete CI log-summary text
including source-scope disclaimer, selected certificate evidence, risk flags,
truncated checks and failure reasons. Its 128 seeded byte-for-byte tests
compare with `render_ci_log_summary` from the original Python module, plus
malformed-input cases. Focused CI
[#41974105096](https://github.com/joeyst8/witnora-core/actions/runs/41974105096)
and full Rust CI
[#41974105868](https://github.com/joeyst8/witnora-core/actions/runs/41974105868)
passed. This moves only deterministic formatting into Rust:
release verification, trust-card construction, artifact writes and GitHub
output integration still require the Python verifier and are **not** claimed
to be ported. The source-file ledger remains 466 not migrated, 80 parallel
Rust implementations and 14 partial-native verified; this extension of
`ci.py` does not count as another newly ported Python source.

## Python test oracle decision

See [`PYTHON_ORACLE_RETENTION.md`](PYTHON_ORACLE_RETENTION.md). The original
295 Python tests are retained while Rust differential tests, independent
DRAT/Lean/source-CNF gates and malicious-input validation remain necessary.
The repository contains additional migration tests beyond that baseline.

## Migration wave 7: native verification presentation layer (verified subset)

Source: `witnora_core/verification_report.py` (unmigrated before wave 7).
Rust candidate: `rust/witnora-ve/src/verification_view.rs`, exposed via the
Python-free `witnora_verification_view` executable. Three pure presentation
operations are reproduced: report-to-trust-card projection, trust-card
Markdown, and verification-report Markdown. Seeded byte/parity tests compare
128 realistic verification records with the independent Python renderer,
including partial replay scope disclaimers, proof-selection risk flags,
checker lists, artifact hashes, and malformed JSON rejection. Focused CI
[#41977249209](https://github.com/joeyst8/witnora-core/actions/runs/41977249209)
and full Rust CI
[#41977249249](https://github.com/joeyst8/witnora-core/actions/runs/41977249249)
passed.

**Boundary:** this is not source-CNF verification, independent `drat-trim`,
Lean proof checking, certificate validation, archive extraction, or full
release-verification orchestration. Those Python paths remain required.
The source ledger now records `verification_report.py` as
`parallel_reference`, because only presentation is ported. Current counts:
465 not migrated, 81 parallel Rust references, 14 partial-native verified.

## Migration wave 8: native artifact SHA-256 integrity check (candidate)

Same source: `witnora_core/verification_report.py`. A separate Python-free
`witnora_evidence_check` CLI reproduces the artifact integrity subset:
streamed uppercase SHA-256 file hashing, release-manifest Markdown hash-table
parsing, source-path/name lookups and `MATCH`/`MISMATCH`/`MISSING` status.
Its differential gate compares 128 seeded binary files, a 1 MiB boundary
case, expected-hash casing, missing files and malformed manifests with the
Python verifier helpers. It is **not** independent proof checking and must
never promote a mere hash match into SAT or UNSAT certification. CI is pending.

## Next dependency-aware work

1. Finish and independently verify the remaining CI CLI/report orchestration,
   which still has Python-only code despite the verified policy subset.
2. Prioritize reproducible, side-effect-free verification/reporting helpers
   with explicit semantics, adding Rust-native tests and Python differential
   controls before switching defaults.
3. Tackle the remaining 54 unmigrated core modules, and review the 80 parallel
   and 14 partial modules based on runtime dependency and soundness risk rather
   than filename count alone.
4. Track CLI, benchmark scripts and tests separately; preserve independent
   checkers where they are required for certification.

No new claim of full migration or a general SAT complexity theorem is made.
