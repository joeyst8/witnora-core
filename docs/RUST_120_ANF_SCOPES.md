# R-120: native arbitrary-width ANF equation scopes

`polynomial_scopes(equations, backend="rust")` now produces exact decimal
`BigUint` scope masks for each equation in Rust, with Python converting the
masks back to integers. Empty/constant equations have scope zero; invalid
nonpositive variable IDs are rejected.

The default Python implementation remains the reference. Focused differential
CI covers 350 seeded equation systems, including variable IDs 180 and 300,
plus constant and invalid-input cases. The migration has no bearing on
polynomial-time SAT or a proof of TC-063. Native CI is required.
