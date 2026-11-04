# R-088: graph-expression conjecture mining in Rust

The native implementation generates the same atomic/compound grammar, exact
integer expression evaluations, training graph signatures, equality candidates,
complexity/label ordering, and holdout counterexamples as the Python reference.
Graph sample generation and graph metrics remain in their previously established
Python sources. The entry point defaults to the Python implementation and
allows `backend="rust"` for the computational candidate-search pathway.

The focused regression compares 180 seeded expression evaluations and three
complete holdout reports with varied candidate limits. Surviving equalities
are explicitly unreviewed finite examples; neither novelty nor Lean theorem
status is inferred.

Status: native compilation, wheel build and focused differential comparisons passed
in GitHub Actions run #41920638984.
