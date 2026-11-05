# R-167–R-170: mixed nonlinear source-CNF and cap stress

This follow-on proof experiment adds 160 held-out, deterministic complete
contradictory XOR witnesses (arity 1–3) embedded in four source families:

- **R-167:** disjoint signed nonlinear background clauses.
- **R-168:** signed nonlinear clauses overlapping the XOR variables.
- **R-169:** duplicated and permuted original source clauses.
- **R-170:** deliberately tight clause-count and proof-byte caps.

The native and Python row-trace candidates must match exactly, including
success/failure category and statistics. Every produced proof must pass the
independent Python RUP-subset checker from the original full CNF. The tester
does not relax source-witness requirements, DRAT verification or Lean trust.

**Status: held-out differential CI pending.** These are still small structured
UNSAT instances, not general SAT or #SAT performance evidence.
