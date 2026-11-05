# R-115: exact clause violation indicator in Rust

`clause_violation_polynomial(clause, backend="rust")` now compiles an entire
signed clause through one PyO3 call. The native kernel applies the Boolean
ring identities `x_i**2 = x_i` and `1 + x_i` for positive literals, and
uses XOR cancellation for parity. Empty clauses evaluate to polynomial ONE;
clauses with both signs of the same variable reduce to polynomial ZERO.

The default Python implementation is unchanged. Native differential tests
cover 400 seeded mixed clauses, repeated and contradictory literals, and
variable IDs above 128. The Rust wheel gate remains required for verification.
