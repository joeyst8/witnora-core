# R-071 — Exact parity-spoke source recognizer (pending native verification)

The restricted `spoke_collapse.py` family now offers explicit opt-in Rust
backends for source CNF construction, exact-source classification, and
deterministic family assembly. The native generator builds the exact signed
2-XOR gadget clauses and canonicalizes the result, refusing duplicate middle
variables or invalid spoke parity fields. The classifier refuses any CNF that
does not exactly match the generated source (no general SAT decision claim).

The native result distinguishes contradictory boundary syndromes with the
first conflicting indices, or produces the exact satisfying assignment when
all boundary syndromes agree. Python preserves the public `ParitySpoke` data
type and output metadata and remains the default reference backend.

The focused CI includes 500 seeded random families, mutated-source rejection,
12 finite brute-model-enumeration family cases, plus direct Rust unit tests.
Do not mark this module verified until the compiled Rust wheel and tests pass.
Existing Lean theorem provenance is independent of these software tests.
