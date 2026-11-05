# R-118: native ANF geometry report

`analyze_parity_anf(..., backend="rust")` retains source CNF and sketch
validation in Python, then invokes Rust to build the parity equations and
compute all eight geometry fields (dimensions, monomial occurrences,
post-XOR monomial counts, zero rows, degree and distinct nonzero equations).

Focused CI compares 216 seeded geometry reports with the default Python
path. This is a descriptive statistic of a parity relaxation, not evidence
that the relaxation is equivalent to the original source CNF. The PyO3
wheel and comparison gate must pass before claiming the milestone verified.
