# R-060 — Targeted graph-family constructors (partial native port, pending CI)

The deterministic finite-family constructors `cycle`, `wheel`,
`complete_bipartite` and `mycielski_c5` have an opt-in Rust implementation.
The Python default and all counterexample evaluation, random generation,
reporting and proof-status fields remain untouched.

`tests/test_targeted_graph_families_rust.py` checks 97 cycles, 96 wheels,
196 bipartite parameter pairs, the 11-vertex Mycielski graph, and rejection
of invalid parameters. Native tests must run in GitHub Actions; local Rust
toolchain/PyO3 extension is unavailable. This is **not** a complete port of
`targeted_graph_theorems.py` and is **not** a verified migrated file.

These fixed graph examples are finite empirical controls and do not constitute
a graph theorem, Lean proof, or evidence of novelty.

## Verification update

The R-060 native differential step passed in [Rust Actions run #41868308092](https://github.com/joeyst8/witnora-core/actions/runs/41868308092).
Only the four graph constructors are native; the search remains Python.
