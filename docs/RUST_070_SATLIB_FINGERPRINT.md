# R-070 — SAT library structural fingerprint (pending native CI)

The Python structural fingerprint now supports an opt-in `backend="rust"`.
Rust implements the basic deterministic metrics: numbers of distinct variables
and canonical clauses, maximum clause width, counts of unit/binary/ternary
clauses, primal graph connected components, largest variable occurrence count,
and number of mixed-polarity variables.

Python still owns the source SHA-256 digest, its exact two-XOR pattern detector,
six-place mixed-polarity rounding, and the observational-only report fields.
This is an intentionally **partial native implementation** until the residual
XOR detector and final report construction are also migrated.

Validation: Rust unit tests for empty, disconnected, and mixed-polarity cases;
400 reproducible randomized canonical CNFs checked against the independent
Python reference, including empty clauses and tautologies in raw input.
The focused native workflow must pass before marking this module as native
verified. This code does not issue proof or algorithmic novelty claims.
