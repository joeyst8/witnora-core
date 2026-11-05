# Witnora Python test retention during Rust migration

## Decision

**Retain the original Python test corpus while the Rust runtime is being
migrated.** Python is still an independent reference implementation and
must not be deleted or re-labelled as fully migrated merely because Rust
passes the same fixtures. Treat tests as separate validation assets, not
runtime modules that can all be blindly converted.

The source ledger tracks **295 original** `tests/*.py` files. The current
workspace has **463** `tests/test_*.py` paths, including **140** additional
filenames ending `_rust.py` that serve migration/differential verification.
These are different denominators: the original 560-file ledger should not
be represented as the current total number of Python files in the repository.

## Retention rules by trust boundary

| Category | Concrete tests | Decision |
|---|---|---|
| Independent `drat-trim` / DRAT evidence | `tests/test_real_drat_trim_smoke.py`, `tests/test_drat_trim_integration.py`, `tests/test_drat_coverage_hardening.py`, `tests/test_tseitin_xor_drat.py` | Retain an independent external checker; Rust may produce evidence but cannot validate its own UNSAT assertion as the sole authority. |
| Lean proof / source-residual gate | `tests/test_lean_cnf_gate.py`, `tests/test_lean_parity_compression_gate.py`, `tests/test_lean_g5_gate.py`, `tests/test_lean_g14_gate.py` | Retain proof-kernel checks and rejected-source/mutation cases; do not replace with Rust parser acceptance alone. |
| Certificate and original-source invariants | `tests/test_certificate_export.py`, `tests/test_ascii_certificate_adversarial.py`, `tests/test_proof_trace.py`, `tests/test_proof_obligation_matrix.py` | Retain independent byte/provenance checks against the exact original CNF and certificate. |
| Migration differential tests | `tests/test_ci_native_policy_migration.py`, `tests/test_report_native_migration.py`, `tests/test_report_standalone_rust_cli.py`, `tests/test_compare_standalone_rust_cli.py`, `tests/test_claims_standalone_rust_cli.py`, `tests/test_artifact_summary_standalone_rust_cli.py`, `tests/test_ci_summary_standalone_rust_cli.py` | Keep as Python-vs-Rust reference gates during migration and release qualification. |
| Ordinary Python unit tests of non-proof helpers | All remaining original tests after explicit function-by-function mapping | Potential eventual Rust-unit-test replacement, **not yet approved**: first verify edge cases, error behavior, independent oracle and native-default parity. |

The original ledger has **54** test filenames matching
`lean|drat|proof|certificate|source_identity|source_parser`. This is a
conservative discovery hint, **not** a proof that exactly 54 tests are
soundness-critical: other filenames can cover the same boundary, and
the 140 new Rust-suffixed tests can also contain mandatory checks.

## Release / retirement gate

For each test proposed for retirement, record all of the following:

1. Its original Python behavior and the exact Rust-native test(s) covering it.
2. The independently checked mathematical/certificate trust boundary, if any.
3. Hostile tests for malformed certificates, wrong source identity,
   contradictory proof evidence, resource caps, and incorrect SAT models.
4. Full focused CI, native Rust CI and external `drat-trim`/Lean outcomes.
5. The reviewer-approved choice to retain the Python oracle, maintain a
   second-language oracle, or replace a genuinely redundant unit test.

No test deletion, proof authority transfer, native-default switch or
release approval is part of this checkpoint. Research gate `R-500` is
still a verification milestone, **not** 500 migrated Python sources.
