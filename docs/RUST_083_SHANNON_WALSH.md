# R-083: bounded Shannon/Walsh recursion in Rust

`witnora_core/crc_shannon_oracle.py` retains the Python reference by default.
The Rust counterpart now canonicalizes normalized source clauses, performs
exact memoized Shannon cofactors, preserves the Python unit-first / frequency
branch policy, tracks memo hits and state caps, and emits exact arbitrary-size
signed Walsh coefficients. State-budget exhaustion returns `None`.

The differential suite compares 160 seeded overlapping CNFs at variable
budgets from 1 to 8, restricted state budgets, empty and contradictory CNFs,
and sparse global variable IDs up to 256. CI also reruns all preceding native
source comparisons. This recursion remains exponential in the worst case and
is not a Lean-certified polynomial SAT algorithm.

Verified: **focused Rust CI #41916191993 passed** native library tests,
the Python-accessible wheel and all prior focused source comparisons. The
manifest records R-083 as `parallel_reference`.
