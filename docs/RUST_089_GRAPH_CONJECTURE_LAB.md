# R-089: bounded graph-invariant conjecture laboratory

Rust now computes the exact bounded graph invariants (`alpha`, `tau`, `omega`,
`chi`, `nu`, maximum degree), enumerates comparison/additive templates, checks
training signatures and returns first holdout counterexamples. Python retains
deterministic graph-mask sample generation for both backends; this avoids
silently changing the frozen seeded experiment. Default Python behavior is
unchanged, with explicit `backend="rust"` on graph metrics and study entry
points.

The differential gate checks 500 seeded graphs, including larger bounded
graphs, invalid-input rejection and three full experimental reports. CI must
compile the Rust extension and run all comparisons before the migration
manifest can promote R-089.

These are finite-graph hypotheses, not proved theorems or verified novelty.

Status: awaiting compiled native CI.
