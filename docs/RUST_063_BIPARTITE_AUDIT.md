# R-063 — Bipartite partition audit (partial native port, pending CI)

The deterministic BFS two-coloring function used in the finite DSATUR audit
now has an opt-in Rust implementation. Every disconnected component starts
with color zero; sorted neighbor order preserves the Python reference's exact
color assignment, not merely its bipartite/nonbipartite verdict.

The native gate enumerates every simple graph with up to five vertices and
compares exact partitions, plus 500 seeded random graphs up to 30 vertices,
self-loop, invalid-endpoint, and empty-graph controls. The Rust entry point
caps graphs at 4096 vertices and rejects out-of-range indices.

`run_bipartite_audit` and the DSATUR greedy coloring function remain Python.
This is a **partial source module**, not a verified completed migration until
native CI passes. It is a finite implementation audit of a known graph fact,
not a new theorem, Lean proof, or complexity claim.

## Verification update

[Rust Actions run #41870670521](https://github.com/joeyst8/witnora-core/actions/runs/41870670521)
completed successfully, including the R-063 native BFS partition differential
step. The bipartition function is verified in parallel; the full DSATUR audit
is still Python, and the file remains a partial-native-verified module.
