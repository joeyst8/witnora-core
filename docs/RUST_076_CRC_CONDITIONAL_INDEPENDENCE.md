# R-076 — Exact source-conditioned structural independence (pending CI)

The optional native Rust backend validates the offered full source model,
conditions exact signed CNF on a separator assignment, and invokes the
source-relative structural independence checker on the residual formula.
It preserves independent group membership constraints, source-clause and
residual-clause counts, and a 256-bit boundary witness without truncation.

A `false` structural result is inconclusive, not a claim of dependence.
No new theorem, general SAT result or Lean verification is claimed.

The focused differential suite compares 350 seeded source families twice
(planted valid and invalid witnesses), plus high-bit and empty-clause
controls, against the default Python implementation. Promotion requires
compiled Rust tests and exact report parity.
