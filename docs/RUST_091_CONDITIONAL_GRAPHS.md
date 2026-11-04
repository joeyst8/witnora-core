# R-091: conditional and transformed graph conjecture screening

Native Rust enumerates the fixed 58-template grammar, checks non-vacuity,
tests training records, and identifies the earliest holdout counterexample.
The opt-in `backend="rust"` uses the same Python-generated graph samples and
exact invariant records as the default Python implementation. This preserves
seed selection, graph ordering, and the established finite experiment scope.

Differential CI checks four complete bounded reports plus empty-training
edge cases. Passing the gate validates implementation parity, not mathematical
novelty, Lean proof, or universal conjecture truth.

Status: awaiting native GitHub CI.
