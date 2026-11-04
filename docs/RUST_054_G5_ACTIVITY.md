# R-054 — Native G5 elimination-activity and cross-merge ranking

**Status:** Green, 2026-11-04. Full CI: https://github.com/joeyst8/witnora-core/actions/runs/41845381144

## Port

- Python source: `witnora_core/g5_elimination_activity.py`.
- Native Rust: `rust/witnora-ve/src/g5_elimination_activity.rs`.
- Opt-in adapters for `activity_from_g5_operations_rust`, `ranked_pair_candidates_rust`, `pairwise_cross_merge_activity_rust`.
- Full regression gate: `tests/test_g5_activity_rust.py` in `.github/workflows/rust-ve.yml`.

The Rust operator counts touches from the union of target/source supports, cancellations from their intersection, and pair cross-merges only when the two vertices occur exclusively on opposite sides of an XOR step. Swap steps are ignored; original positive unique coefficient validation, source-universe constraints, deterministic tie-breaking, full pair output and fail-closed errors are preserved.

## Verification

- 1,000 seeded random operation streams across universe sizes 0–19, with exact Python/Rust report and score comparisons.
- A separate direct per-variable and per-pair scorer independently recomputes all touches, cancellations, XOR counts, cross-merge scores and event totals.
- Exhaustive pair coverage plus 0-, finite-, and unlimited ranking policies; invalid operations, duplicated/noninteger/out-of-universe coefficients and malformed limits rejected.
- Native compiler/unit tests, PyO3 extension, and full R-001–R-054 differential CI passed.

## Claim boundary

These are diagnostic ranks only. Neither observed frequency nor a high-scoring pair proves a separator, satisfiability, G14, or Lean kernel soundness. Python default code and all existing Lean trust checks remain unchanged. Ledger after R-054: **42 parallel Rust ports, 518 remaining, 0 Python retired**.
