# R-053 — Native sparse GF(2) original-row basis

**Status:** Green, 2026-11-04. Full CI: https://github.com/joeyst8/witnora-core/actions/runs/41844229274

## Source equivalence boundary

- Original reference: `witnora_core/gf2_sparse_row_basis.py`.
- Rust implementation: `rust/witnora-ve/src/gf2_sparse_row_basis.rs`.
- Opt-in Python adapters: `row_mask_rust`, `build_sparse_parity_basis_rust`, `verify_sparse_parity_basis_rust`, and `accepts_masks_rust`.
- Tests: `tests/test_sparse_basis_rust.py`; build and regression: `.github/workflows/rust-ve.yml`.

The Rust builder chooses an independent subset of **original sparse parity rows** without widening them; it retains exact source indices and produces arbitrarily large bitset witnesses showing each discarded row is an XOR of selected rows. The Rust verifier independently reconstructs every source row and checks retained identity witnesses, dimensions, source-row identity, and GF(2) rank. Decimal-encoded BigUint across PyO3 avoids the 64-bit mask ceiling. Python remains the production reference/default.

## Verification details

- 600 seeded synthetic sparse sketches, each checked under two deterministic orderings (1,200 exact Python/Rust certificate comparisons).
- Independent per-row parity-oracle enumeration for clause counts <=8, plus random larger masks.
- A 150-clause, rank-130 sketch checks expansions larger than 128 bits, including dependent and empty rows.
- Tampered counts, source IDs, rows, coefficient expressions, invalid source row bounds, and unsupported ordering are rejected.
- Rust unit tests, extension build and the full existing R-001–R-053 regression pipeline passed.

## Scientific limits

An XOR basis certificate proves equivalence **among the supplied parity constraints** for every violation vector. If those parity constraints are an inexact sketch of source CNF, it does not prove source-CNF equivalence, SAT solving, a complexity-class result, or a Lean theorem. No original Python file was retired and no Lean trust gate changed. After R-053: **41 of 560** files have verified parallel Rust counterparts; **519 pending**, **0 retired**.
