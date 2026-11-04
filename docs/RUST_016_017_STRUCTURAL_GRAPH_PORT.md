# Witnora R-016/R-017: Native Structural Graph and Treewidth

Research date: November 4, 2026. Unmerged draft PR #122.
All code is opt-in; Python remains an independent reference.

## R-016: primal graphs and incidence components

`rust/witnora-ve/src/graph.rs` provides:

- canonical primal-variable and graph-edge extraction from CNF;
- incidence-graph connected components with stable clause order;
- correct treatment of empty clauses, isolated variables appearing
  in source clauses, and tautological/duplicate source normalization.

The original Python APIs now accept `backend="rust"`:

- `primal_graph(formula, backend="rust")`
- `connected_components(formula, backend="rust")`
- `component_details(formula, backend="rust")`

[Green R-016 CI #41746679206](https://github.com/joeyst8/witnora-core/actions/runs/41746679206):
**1,200 seeded exact source comparisons** to the unchanged Python
primal graphs, component assignments, canonical hashes, clause indices
and incidence-edge records. Native Rust unit tests passed.

## R-017: complete bounded-width elimination-order search

`rust/witnora-ve/src/treewidth.rs` implements the same deterministic
candidate ordering, exact fill-in, failed-state memoization and
independent order verification as the original bounded-width Python
code. Supported exact target widths remain **0 through 4**.

- `find_elimination_order(graph, c, backend="rust")`
- `verify_elimination_order(graph, order, backend="rust")`

The native search has an explicit maximum-state budget; exceeding it
raises an error and **does not** claim that no width-c elimination
order exists. Successful native orders are re-verified by the original
Python width calculator during the transitional API phase.

[Green R-017 CI #41746920843](https://github.com/joeyst8/witnora-core/actions/runs/41746920843):
**1,000 seeded small-graph order/width comparisons** and native
exhaustive checks on paths, cycles, cliques, invalid orders and cap
refusals.

## What is not yet migrated

These Rust functions cover two foundational graph modules plus
treewidth ordering, not the whole graph and proof ecosystem.
Still outstanding are the higher-level branch planners, separator
logic, reconstruction, proof certificates, Lean gateways, research
scripts, tests and release workflows.

The file-by-file baseline manifest remains at
`research/python_to_rust_manifest.json`. No original Python file
has been removed; no claim of a new complexity theorem is implied by
these conventional exact algorithms.
