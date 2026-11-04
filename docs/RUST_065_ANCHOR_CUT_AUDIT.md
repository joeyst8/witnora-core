# R-065 — Full-CNF anchor cut reachability (partial native, pending CI)

The opt-in native implementation builds the full source-CNF primal graph
after removing a candidate vertex cut and checks whether a left anchor can
reach a right anchor. It reproduces Python's behavior on excluded anchors,
missing anchors, disconnected components, and signed clauses. Zero literals
are rejected at the native boundary.

The differential gate enumerates all simple graphs with 1..4 vertices as
binary source clauses, anchor pairs and multiple cuts, plus 700 seeded random
signed source-CNFs and cuts. Python remains the default; hidden separator
generation and the independent parity-cut-width oracle remain Python.

This is a source-bound graph diagnostic, not a SAT/UNSAT proof, Lean
certificate, or demonstration of mathematical novelty. Native CI is pending,
and the entire Python source file is not fully migrated.

## Verification update

[Rust Actions run #41872605604](https://github.com/joeyst8/witnora-core/actions/runs/41872605604)
completed successfully, including R-065's native full-CNF reachability gate.
This function is verified, while additional source functions remain Python or
await native checks.
