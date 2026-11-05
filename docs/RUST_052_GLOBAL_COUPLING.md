# R-052 — Native exact two-edge-cut graph witnesses

**Status:** Green, 2026-11-04. Full CI: https://github.com/joeyst8/witnora-core/actions/runs/41842971721

## Scope and precise invariant

- Original reference: `witnora_core/global_coupling_separator.py`.
- Native module: `rust/witnora-ve/src/global_coupling_separator.rs`.
- Opt-in adapters: `two_edge_cut_boundary_pairs_rust`, `prioritized_global_pairs_rust`.
- Full CI: `tests/test_global_coupling_rust.py` and `.github/workflows/rust-ve.yml`.

The native operator reproduces sorted edge enumeration, exhaustive unordered two-edge deletions, exact two-component tests, crossing-edge validation, each partition's distinct endpoint boundary, independent deletion of the two candidate separator vertices, witness metadata and deterministic residual-balance priority. Disconnected inputs are skipped; malformed or asymmetric graphs are rejected. Exhaustive vertex-pair fallback is preserved.

## Verification

- 900 reproducible random undirected graphs (including empty, disconnected and dense cases) checked for exact Python/Rust reports and priorities.
- 100 planted cycle-family controls checked for exact candidate-witness parity.
- An independent breadth-first graph oracle verifies that each claimed two-edge cut really gives two components, both edges cross the cut, separator deletion disconnects the source graph, reported split sizes and exhaustive pair count are exact.
- Rust compiler unit tests, Python binding compilation, and the entire R-001–R-052 regression workflow passed.

## Trust boundary

Graph diagnostics are not a G14 theorem, a SAT solution, a better asymptotic complexity claim, or a Lean certificate. No default Python algorithm, trusted gate, or Lean artifact was removed or bypassed. R-052 marks the file as a verified **parallel** Rust counterpart, not a completed retirement. Ledger: **40/560 parallel**, **520 pending**, **0 retired**.
