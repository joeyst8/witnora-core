# R-122–R-123: native XOR evaluation and substitution

`XorEquation.evaluate(assignment, backend="rust")` evaluates exactly the
parity equation on available assigned variables and returns `None` for
incomplete assignments. `XorEquation.substitute(..., backend="rust")`
removes assigned variables and updates the parity RHS in one Rust call,
then rebuilds the Python equation with all source/detection metadata.

Each primitive has 500 deterministic seeded differential cases, with
large variable IDs and partial assignments. Python remains the default
and source trust metadata is not downgraded. CI must pass the Rust wheel,
unit tests and exact comparisons before these milestones are verified.
