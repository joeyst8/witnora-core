# R-117: batch native parity-row equation construction

`row_violation_polynomials(..., backend="rust")` now validates the sketch and
optional basis in Python, then combines already compiled source clause
indicators in one Rust `anf_row_violations_native` call. The native routine
XORs all selected clause polynomials for each row and fails for an invalid
clause index.

Focused differential coverage compares the resulting immutable ANF rows
for 162 seeded CNFs, both in original sketch order and basis-reduced order.
The Python route stays the default; Rust wheel CI is needed for verification.
