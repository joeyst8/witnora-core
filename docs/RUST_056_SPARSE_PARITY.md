# R-056 — Native sparse odd-column checks and finite audits

**Status:** Green, 2026-11-04. Full CI: https://github.com/joeyst8/witnora-core/actions/runs/41860781144

## What moved

- Source: `witnora_core/sparse_parity_checks.py`.
- Rust: `rust/witnora-ve/src/sparse_parity_checks.rs`.
- Opt-in adapters: native `column_signatures`, `build_sparse_odd_sketch`, `validate_sparse_odd_sketch`, `low_weight_collisions`, `source_row_scope`, `audit_sparse_small`, and `min_degree_elimination_width` counterparts (all with `_rust` suffix).
- Full CI: `tests/test_sparse_parity_checks_rust.py`.

The native builder chooses exactly three row positions per clause, keeps distinct odd-weight column signatures, obeys row-width limits and fails closed on unsuccessful bounded attempts. Its seeded jitter values are supplied by the **original Python `random.Random(seed)`** at the interoperability boundary so that it reproduces the legacy Mersenne Twister sequences exactly. Source normalization/digest remains in the Python adapter. The placement, structural matrix validation, arbitrary-width bit signatures, low-weight collision counting, finite assignment audit, clause-scope sizes, and minimum-degree induced-width heuristic run in Rust.

## Independent verification

- 400 seeded random source CNFs: identical generated row matrices, source identity, structural metadata and low-weight collision counts against the original Python implementation.
- Independent direct Boolean enumeration reproduces source model counts, nonmodel counts and parity-sketch false positives.
- 300 independent synthetic factor-scope graphs check exact minimum-degree width parity and clique bounds.
- Tampered source digest or row shape, invalid bounds, zero budgets, malformed scopes fail closed.
- Existing R-001–R-055 tests and the new R-056 test all passed under Rust build, PyO3 and GitHub Actions.

## Limits and migration status

The guarantee is only that arbitrary violation vectors of weights 1, 2 and 3 cannot evade all degree-three distinct odd-column checks. Larger supports may collide, and no source-CNF equivalence or SAT algorithmic complexity claim follows. The opt-in adapter still delegates seeded RNG generation and source normalization to Python: this is a verified **parallel native computation path**, not a Python retirement or a purely Rust runtime. Existing Python defaults and Lean gates stay intact. After R-056: **44 verified parallel ports, 516 files pending, 0 retired**.
