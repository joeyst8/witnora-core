# Witnora R-014/R-015: Native RUP-Only Proof Path

Research date: November 4, 2026. Draft PR #122; not merged.  
TC-063 Lean proof kernel PR #121 remains untouched.

## Verified R-014: independent Rust replay

The new `rust/witnora-ve/src/rup_checker.rs` module
implements **RUP-subset** DRAT-style proof replay over the exact original
canonical CNF database. The checker:

- parses additions and deletions while rejecting malformed/tautological
  proof clauses;
- applies explicit assumptions consisting of the negated candidate
  clause;
- carries out deterministic iterative unit propagation;
- confirms every addition is RUP-checkable, then derives the
  empty clause before accepting;
- checks strict/non-strict deletions, diagnostics, warning order, and
  failed-proof line numbers.

[Green CI #41746152046](https://github.com/joeyst8/witnora-core/actions/runs/41746152046)
passed the Rust unit tests and **1,200 randomized comparisons** with
Witnora's unchanged original Python
`witnora_core/drat_check.py`. The Python integration is opt-in
through `check_drat_text(original_formula, proof_text, backend="rust")`.
The original Python checker remains the default.

## R-015: standalone Rust RUP proof-file command

The native executable now provides:

```sh
rust/witnora-ve/target/release/witnora-ve \
  --check-rup original.dimacs proof.drat
```

Exit status 0 indicates a verified RUP-subset derivation of the empty
clause; 1 indicates an invalid/incomplete proof; 2 indicates malformed
input/operational errors. Output identifies only
`s VERIFIED_RUP_SUBSET` or `s INVALID_RUP_SUBSET`.

The standalone command reads and canonicalizes the original DIMACS
text in Rust and performs all proof replay there; no Python wheel is
needed. [Green R-015 CI #41746389876](https://github.com/joeyst8/witnora-core/actions/runs/41746389876)
verified an actual file-based valid proof and a deliberately false proof,
including the required nonzero exit status for the latter.

## Important trust limitations

- The algorithm is only RUP-subset replay. It does **not** check
  arbitrary DRAT/RAT additions; an input using unsupported proof
  formats must not be called verified on the basis of this tool.
- Passing differential and unit tests does not formalize the Rust
  checker in Lean, and does not prove Rust source soundness. The
  Lean `GeneralRUP` certificate kernel remains the trusted
  formal verification boundary for TC-063.
- External `drat-trim` has not been removed. Existing Python
  code still orchestrates its independent external checks.
- A full repository-wide Python-to-Rust transition includes hundreds
  of modules/scripts/tests outside this RUP-only path. The original
  Python proof path is preserved until exact parity, formal trust,
  and release/workflow changes are independently reviewed.

See `docs/RUST_009_013_CORE_PROOF_MIGRATION.md` and
`research/python_to_rust_manifest.json` for broader coverage.
