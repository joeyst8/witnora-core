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

## Verification update

[Rust Actions run #41873131617](https://github.com/joeyst8/witnora-core/actions/runs/41873131617)
completed successfully, including the R-066 native differential gate. The
support-cut oracle is now verified as a native function, while the complete
Python source-module migration still awaits the R-067 generator gate.
