# R-070 — SAT library structural fingerprint (partial native verified)

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
five exact independent fixed-metric fixtures; 400 reproducible randomized
canonical CNFs checked against the Python reference, including empty clauses
and tautologies in raw input.
[Focused CI #41882663537](https://github.com/joeyst8/witnora-core/actions/runs/41882663537) passed Rust unit tests, wheel build, and the R-070 comparisons.
Only the structural metrics are native; the complete source file is **not**
fully migrated and does not yet count toward the 50-file batch target. This code does not issue proof or algorithmic novelty claims.
