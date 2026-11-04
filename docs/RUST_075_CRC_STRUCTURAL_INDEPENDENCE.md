# R-075 — Exact source-relative structural independence (native CI pending)

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
