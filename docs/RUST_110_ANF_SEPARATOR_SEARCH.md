# R-110: full native bounded ANF separator selection

The Rust `anf_find_bounded_separator_native` reproduces the Python candidate
ordering, variable-degree pool limiting, component-balance score, tie breaks,
and exact candidate-check budget. It reuses R-109's arbitrary-width residual
component routine rather than truncating variable bitmasks.

`find_bounded_separator(..., backend="rust")` is an opt-in direct native
search. Focused CI compares 135 seeded inputs, including large variable IDs,
and rejects invalid budgets. Separator-conditioned counting still uses its
original Python structured counter and is not a new complexity theorem.
