# R-099: Rust Kempe component swaps

`kempe_swaps_native` enumerates the two-color component swaps, including
canonical order, duplicate-coloring removal and a checked proper-coloring
invariant. Python remains the default; `kempe_swaps(..., backend="rust")`
opts in. `kempe_repair(..., backend="rust")` combines native swaps with the
R-098 native bounded recoloring routine while retaining its small Python
control loop. Experiment sampling remains Python.

The CI native wheel runs exact-output differential tests on seeded graphs and
limited repair budgets. These are empirical implementation comparisons, not
completeness, mathematical novelty, or Lean-kernel proofs.
