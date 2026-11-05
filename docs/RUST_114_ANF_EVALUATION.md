# R-114: arbitrary-width ANF polynomial evaluation

`evaluate_polynomial(poly, bits, backend="rust")` now calls native Rust
`anf_evaluate_native`, which evaluates the Boolean multilinear GF(2) sum
at the specified nonnegative assignment bitmask. Variable IDs are 1-based;
variable 1 corresponds to the least significant bit. The Rust implementation
parses decimal `BigUint` inputs and does not impose a 64- or 128-bit limit.

The Python implementation remains the default/reference. Focused differential
tests compare 350 seeded polynomial/assignment pairs and constants,
including variable 257. This computes only the value at one assignment; it
is not evidence for a polynomial-time counting method or a new complexity
theorem. Native wheel CI must pass before the milestone is verified.
