# PR #119: Full-CNF adjacency cache — preliminary performance evidence

Status: **experimental speed improvement; no solver advantage or novelty claim**.

## Change

`discover_repaired_separator` previously rebuilt the original CNF primal
graph for each candidate cut. The new implementation constructs the graph
once per search and traverses the vertex-deleted graph for each candidate.
Deleting vertices from a precomputed primal graph has the same connectivity
as rebuilding the primal graph from each clause after deleting those vertices.

## Correctness checks

- 256 deterministic randomized CNFs and variable-removal sets independently
  compared component connectivity from cached adjacency against direct
  clause-by-clause reconstruction of the surviving graph.
- The existing autonomous-parity and parity-cut boundary test suites passed.
- Every result dictionary matched the previous implementation for all 56
  formulas in the established seven-family study.

## Paired microbenchmark

Environment: one local Python process, same host and formulas, 9 repetitions
per case, alternating which implementation ran first. The previous code was
loaded from the pre-optimization local commit `39032b8` for comparison.

| Metric | Previous | Cached adjacency |
| --- | ---: | ---: |
| Formulas | 56 | 56 |
| Runs per formula | 9 | 9 |
| Cumulative discovery time | 338.36 ms | 210.74 ms |
| Median single-call time | 0.44961 ms | 0.45098 ms |
| Relative cumulative speed | 1.00× | **1.61×** |

These short single-host timings are exploratory and sensitive to runtime
noise. They measure only the Python structural-discovery routine, **not**
end-to-end SAT solving or advantage over MiniSat, Kissat, CaDiCaL, or
CryptoMiniSat. Outcomes and trial counts did not change.

## Negative control

An admissible cut-size pruning check was also tested and discarded: it did
not lower mean candidate trials (11.62 before and after on the 56-formula
study) and increased wall time slightly. It is not part of the patch.
