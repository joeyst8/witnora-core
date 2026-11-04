# R-058 — Native finite clause-violation parity (pending CI)

**Status:** Rust module, Python opt-in adapters, and differential tests committed; full CI not yet verified. Run: https://github.com/joeyst8/witnora-core/actions/runs/41863452092

## Implementation

- Python reference: `witnora_core/eth_clause_violation_parity.py`.
- Rust native module: `rust/witnora-ve/src/eth_clause_violation_parity.rs`.
- Reproduced entry points: SHA-256 compact JSON source digest, arbitrary-bit-width clause-violation masks, parity acceptance of supplied rows, finite greedy separation, exhaustive verification and primal graph completeness.
- Opt-in Python adapter methods retain `_rust` suffix. The frozen seeded `Random.sample` candidate stream remains supplied by Python; greedy selection, 2^n truth-table enumeration and reconstruction run in Rust.
- Tests: `tests/test_finite_parity_rust.py`, including 400 seeded random source-CNF comparisons, independent direct literal evaluation for every assignment, arbitrary-width mask and digest stress for 140 clauses, tamper and budget controls.

## Scientific and operational boundary

This finite enumeration is exponential and has an explicit 1..14-variable bound. A verified finite sketch cannot establish a general SAT solver speedup or new complexity theorem. Python default paths and Lean gates remain unchanged.

**Pending** — not a passing-test or migrated-file claim. GitHub workflow serialized queue is delaying R-057 and R-058. Once run green, update ledger entry for `witnora_core/eth_clause_violation_parity.py`, move R-058 from pending to verified and amend PR #122. Until then, 44 parallel ports, 516 original Python files pending and 0 retired.

## Compiler gate correction (2026-11-04)

The Rust native workflow at commit `c3f2e4266c84e9bfaf38a405246db011595797b6`
failed with E0277 because `sha2`'s finalized byte array did not implement
`LowerHex`. The digest now explicitly formats each byte with two lowercase
hexadecimal digits. This is a build fix only; native differential tests remain
pending until the next CI run completes. No milestone is promoted by this edit.

## Test-oracle correction (2026-11-04)

The next CI build passed compilation and two native differential tests, but
the tampering test incorrectly expected verification to fail when the stated
variable universe grew from 1 to 2 while the source remained `[1] ∧ [-1]`.
An unused second variable does not change unsatisfiability or source/row
equivalence. The invalid-universe negative control now uses nvars=15, beyond
the documented bound; the nvars=2 case is explicitly asserted to pass in
both verifiers. This is a correction to a finite test expectation, not a
relaxation of the verifier or a mathematical theorem.

## Verified Rust gate

**Green:** [Rust Actions run #41868308092](https://github.com/joeyst8/witnora-core/actions/runs/41868308092)
completed successfully, including the exact finite parity comparison,
large-mask controls, and corrected invalid-domain test. R-058 is now a
verified parallel source module: **45 of 560** original Python files have
verified parallel Rust counterparts, **515** are not yet fully verified, and
**zero** are retired. This is not a general SAT theorem or Lean refinement.
