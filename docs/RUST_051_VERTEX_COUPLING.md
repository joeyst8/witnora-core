# R-051 — Native two-vertex graph-cut discovery

**Status:** Green, 2026-11-04. CI: https://github.com/joeyst8/witnora-core/actions/runs/41841546168

## Scope

- Python reference: `witnora_core/vertex_coupling_separator.py`.
- Native Rust: `rust/witnora-ve/src/vertex_coupling_separator.rs`.
- Strict opt-in Python adapters: `vertex_coupling_pairs_rust` and `prioritized_vertex_pairs_rust`.
- Regression: `tests/test_vertex_coupling_rust.py`, wired into `.github/workflows/rust-ve.yml`.

The graph-theoretic reduction enumerates all vertex pairs whose simultaneous removal disconnects a connected graph without existing articulation points. For each removed vertex, reuse R-050's independently checked iterative articulation algorithm. In graphs outside this precondition the report is deliberately incomplete and the exhaustive ordered pair fallback is retained.

## Independent verification

- 900 seeded random undirected graphs with exact Python/Rust report and order comparison.
- 100 cycle-family controls, including larger simple cycles.
- A separate graph component oracle verifies every reported cut, completeness preconditions and no omission of the exhaustive pair order.
- Malformed self-loop and asymmetric adjacency graphs are rejected.

## Trust and migration boundary

The native implementation is diagnostic candidate prioritization only. It neither proves a G14 obstruction nor establishes SAT/UNSAT, improved complexity, or correctness of a Lean artifact. Original Python, default behavior, Lean gates, and exhaustive fallback are retained. The Rust implementation is a verified **parallel reference**, not a Python retirement. After R-051: 39/560 parallel ports, 521 not migrated, 0 retired.
