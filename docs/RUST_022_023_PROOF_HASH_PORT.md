# Witnora Python-to-Rust migration: R-022 and R-023

Status: **GREEN**, dedicated Rust gate
[run 41753697112](https://github.com/joeyst8/witnora-core/actions/runs/41753697112).
Draft PR: [#122](https://github.com/joeyst8/witnora-core/pull/122).
Branch: `research/w-crc-001-asymmetric-v1`.

## R-022 canonical CNF SHA-256

`rust/witnora-ve/src/cnf.rs` computes SHA-256 over the *exact* UTF-8 bytes
of the existing canonical DIMACS rendering. The native `canonical_cnf_hash_native`
PyO3 entry point and `witnora_core/cnf_rust.py:canonical_hash_in_rust`
expose the compatible digest.

`tests/test_cnf_hash_rust.py` checks 1,600 seeded random raw-CNF sources
against the original Python `CNFFormula.formula_hash` property, plus
empty sources, tautologies, duplicates, empty clauses, and invalid signed input.
The CI gate additionally checks the native DIMACS bytes using Python's independent
`hashlib.sha256`.

## R-023 BCE certificate digest

`rust/witnora-ve/src/bce.rs:checked_proof_digest` serializes the existing
BCE evidence as Python-compatible `repr` of an ordered list of tuples containing
the *checked against clause*, *raw sorted resolvent*, and *True/False*.
The result is SHA-256 hashed in Rust and exposed via
`blocked_clause_digest_native`. The opt-in Rust BCE adapter in
`witnora_core/bce.py` no longer assembles or hashes the certificate in Python.
The original Python-only BCE path remains the independent reference.

`tests/test_bce_digest_rust.py` compares 1,200 seeded random proof-row
payloads and explicit edge cases to Python's exact `repr` and
`hashlib.sha256`. The existing R-018/R-019 full witness and simplification
certificate differential tests also run in the same green gate.

## Trust and limits

- Matching a hash does not prove a SAT/UNSAT result; witness checking and
  trusted Lean proof checking remain separate.
- This implementation preserves **specific existing Python certificate bytes**.
  It does not claim a new cryptographic construction.
- Changes are on the draft research branch, not merged into main.
- Python remains the default implementation. The full 560-file migration
  is **not finished**. No original Python modules, scripts, or tests have been
  deleted.
- Adding RustCrypto `sha2` requires dependency/lockfile tracking in the
  long-term release process. CI has built successfully with the dependency.

Next: migrate the complete Python certificate event logger/serializer to a
native Rust representation and compare byte-for-byte hashes and replay order,
while retaining independent verification and Lean trust boundaries.
