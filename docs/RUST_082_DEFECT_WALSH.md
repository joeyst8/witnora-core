# R-082: native defect-hypergraph Walsh oracle

The bounded coherent signed rank-two/rank-three defect oracle now has a Rust
counterpart. It validates source polarity and support structure, enumerates
missing-support cliques under the original resource caps, and returns exact
Walsh coefficients with arbitrary-precision numerator/denominator strings.
The Python `Fraction` conversion and baseline implementation remain intact.

The focused comparison covers 120 seeded rank-two/rank-three near-complete
families, optional free-boundary variables, resource-failure paths and high-bit
boundary validation. This retains an explicit exponential-in-defect cap and
does not claim a generic efficient SAT/counting procedure or Lean proof.

Verified: **focused Rust CI #41913915024 passed** library tests, the Python
native wheel and all focused source-differential comparisons. R-082 is recorded
as `parallel_reference` in the migration manifest.
