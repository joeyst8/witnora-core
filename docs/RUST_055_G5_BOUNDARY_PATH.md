# R-055 — Native G5 provenance boundary-path replay

**Status:** Green, 2026-11-04. Full CI: https://github.com/joeyst8/witnora-core/actions/runs/41846655928

## Port

- Reference: `witnora_core/g5_boundary_path_signal.py`.
- Rust: `rust/witnora-ve/src/g5_boundary_path_signal.rs`.
- Opt-in adapter: `boundary_path_candidates_from_g5_rust`.
- Tests: `tests/test_g5_boundary_path_rust.py` in the complete native differential gate.

Rust replays indexed G5 row swaps and XOR operations over live supports. It cross-checks the actual support before, source and after each operation; matches any supplied post-swap row snapshot; and tracks original edge-equation identities under mod-2 symmetric difference. Only a connected, duplicate-edge-free, edge-simple path with the appropriate degree-one endpoints and degree-two interior yields a candidate. Repeated endpoints, inconsistent snapshots, self-XOR and out-of-range indices fail closed. Deterministic maximum-proxy candidate priority is unchanged.

## Differential and independent checks

- 900 seeded randomized valid indexed swap/XOR streams; exact Python/Rust report and metadata parity.
- 100 planted chain-path streams with intermediate and longer provenance paths.
- Independent replay of original edge IDs plus separate connectivity/vertex-degree/path-balance checks for every emitted candidate.
- Deliberately corrupted XOR after/source snapshots, malformed row indices, incorrect swap snapshot and non-G5 operations rejected.
- Native compiler, Rust unit tests, PyO3 bindings and full R-001–R-055 suite passed.

## Claim boundary

A provenance path is **not** a verified primal/G14 separator: chords and unrelated source edges can invalidate it. No SAT result, asymptotic speedup or Lean theorem follows. Python defaults and all trusted gates remain intact. After R-055, **43/560** original Python files have independently checked parallel Rust ports, **517 not migrated**, **0 retired**.
