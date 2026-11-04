# R-075 — Exact source-relative structural independence (native verified)

The new Rust backend checks normalized signed source clauses, validates
an offered 256-bit boundary assignment, rejects a falsified witness and
computes primal connected components to certify **sufficient** group
independence under that satisfying assignment. Unseparated groups are
inconclusive; Rust never returns a semantic dependence or UNSAT claim.

Python retains the dataclass and is the default reference. The native
checker uses arbitrary-precision unsigned integers, preserving sparse
high-numbered boundary variables without floating-point approximation.

The focused native gate runs 400 seeded source/witness comparisons, empty
and tautological clauses, invalid-input checks and a 256-bit boundary
control. Exact equality with the Python report and rejection semantics is
required before promoting this module. Neither finite tests nor primal
connectivity constitute a general SAT algorithm or a Lean proof.

[Focused CI #41888295075](https://github.com/joeyst8/witnora-core/actions/runs/41888295075)
passed the compiled Rust library, wheel build and R-075 native differential
cases after correcting an earlier BigUint borrow compile error.
