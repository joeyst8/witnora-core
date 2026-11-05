# R-121: canonical XOR support normalization

`_normalize_xor_variables(..., backend="rust")` now delegates GF(2)
occurrence cancellation and sorting to Rust. Each positive variable ID
appears in the resulting support exactly when it appeared an odd number
of times in the input. Python keeps its original `int()` coercion and
input-validation behavior, and remains the default reference.

Focused CI compares 400 seeded variable sequences, repeated, empty and
large-index cases. This is an algebraic primitive, not a new solver
complexity claim or Lean proof refinement. Native CI is required.
