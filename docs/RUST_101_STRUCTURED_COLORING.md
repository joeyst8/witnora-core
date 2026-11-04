# R-101: Rust witnessed greedy-clique bound

`greedy_clique_lower_bound_native` ports the precise deterministic greedy
clique construction and tie-breaking order. A constructed clique gives a
valid *lower bound* on chromatic number; it does not prove optimality unless
matched by a proper coloring with the same number of colors.

`ungated_repair(..., backend="rust")` now routes through R-098, R-099, R-100,
and the new clique routine. Seeded multistart DSATUR and structured-graph
sampling retain Python behavior. The CI differential gate compares the exact
numeric bound and the pipeline outputs against the Python reference.

The research remains experimental, not a novelty or Lean-verification claim.
