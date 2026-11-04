# R-066 — Independent parity support cut-width oracle (pending CI)

An opt-in Rust BFS oracle enumerates small variable subsets of shared equation
supports and returns the smallest cut size whose deletion increases the number
of support-hypergraph components. It mirrors Python's independent finite oracle
without using the production separator detector.

Native fail-closed caps: at most 64 support rows, 16 shared variables, and
cut-size limit 4. Unsupported larger inputs raise a bounded-input error. The
500 deterministic differential test inputs stay inside these bounds and also
exercise empty supports, disconnected components and invalid inputs.

The related full-CNF anchor audit (R-065) passed its own CI. The new R-066
support oracle is pending native CI, and the seeded hidden-separator generator
remains Python. Neither check constitutes a Lean proof or SAT theorem.
