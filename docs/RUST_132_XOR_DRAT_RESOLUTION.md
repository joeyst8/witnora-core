# R-132: native signed-clause resolution helper

`_resolve_fast(a, b, pivot, backend="rust")` now delegates one signed
resolvent step to Rust. It removes the opposite pivot literals,
deduplicates and sorts the resulting clause, and returns `None` for
tautological resolvents. The default Python proof-generation path remains
unchanged, including its existing assumption that inputs are canonical.

Focused CI compares 400 seeded clause-pair resolutions and adversarial
empty/tautology cases. This kernel is a local helper; it does **not**
independently validate a complete DRAT proof, and does not change any
Lean or external proof-checker requirement.
