# R-361–R-380: representation-independent GF(2) witness controls

For each variable, a gauge choice `g_v` transforms `x_v` to `x_v XOR g_v`,
and every XOR equation RHS is adjusted by the parity of its support's gauge
bits. Bijections on variable labels are also applied. This preserves the
inconsistent source-row subsets and the minimum-cardinality witness even
though it changes the syntactic original CNF.

The independent exhaustive GF(2) combinations oracle and original-CNF SAT
truth-table controls agree on 64 paired SAT and 64 paired UNSAT cases. Both
the original and transformed UNSAT proof candidates pass real `drat-trim`.

**Negative finding:** in 20 of 64 UNSAT pairs, the current exporter emits a
different number of proof clauses after the harmless representation change;
the largest absolute difference is 12 clauses. Thus the *witness* selection
is invariant in these tests but the current clausal proof construction has
representation-dependent cost. This is a limitation to investigate.

R-361–R-373 cover identity, polarity and variable-label transformations,
exact original-source encodings, minimal witness, syndrome-state and SAT
equivalence. R-374–R-375 pin the proof-size sensitivity. R-376–R-379 check
external-verifier status and invalid maps/gauges; R-380 replays the full
128-case paired sample. Native Rust differential and independent DRAT gates
run in CI.

**Status:** local reference and independent proof verification passed;
native CI pending. No complete Rust migration, general SAT solver, Lean
theorem or main-branch merge is claimed.
