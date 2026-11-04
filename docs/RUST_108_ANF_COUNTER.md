# R-108: bounded symbolic Shannon count in Rust

The Rust `anf_count_common_zeros_native` implements canonicalized ANF
equation sets, variable-appearance pivot selection, Shannon substitution,
memoization, exact arbitrary-width counts, visit accounting, and fail-closed
search budgets. The Python `count_common_zeros(..., backend="rust")` route
reuses the existing `ANFCountResult` and budget-exceeded exception.

The focused native CI compares bounded answers, number of unique states,
memo hits, maximum equation counts, exhaustion behavior, and a 150-variable
unconstrained count against the Python reference.

This is still exponential in the worst case. The result does not establish
polynomial-time SAT solving, TC-063, a new theorem, or a Lean proof.
