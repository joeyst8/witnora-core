# R-116: batch native source-CNF violation compilation

The opt-in Rust route for `source_violation_polynomials` now validates
and canonically orders the source CNF in Python, then compiles all clauses
in one native `anf_source_violations_native` call. This replaces a loop of
per-clause Python-to-Rust calls while preserving source normalization.

The default Python route is unchanged. Native differential coverage includes
220 seeded CNFs plus empty and contradictory cases. Compilation is exact GF(2)
algebra, not proof of parity sketch equivalence or a SAT speedup theorem.
Verification requires a passing Rust wheel and Python comparison run.
