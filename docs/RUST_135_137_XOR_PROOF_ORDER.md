# R-135–R-137: native XOR proof-order metadata and strategy dispatch

- **R-135:** `_proof_order(..., backend="rust")` preserves Gaussian pivot
  sequence (including duplicates) and appends remaining system variables.
- **R-136:** `_gaussian_order_stats(..., backend="rust")` computes the
  Gaussian order, initial/peak trace widths, and contradiction width
  using native Rust. The trace event metadata and final report schema
  remain compatible with the Python reference.
- **R-137:** `_choose_order(..., backend="rust")` dispatches both Gaussian
  and sparse-min-fill strategies to their native implementations.

The opt-in paths have 160, 130, and 130 seeded differential comparisons,
respectively. The Python reference remains available for independent
cross-comparison; core export defaults have not changed. Passing metadata
parity is **not** equivalent to establishing a valid clausal DRAT proof:
the RUP, `drat-trim`, and Lean verification boundaries remain unchanged.
