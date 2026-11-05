# R-071 — Exact parity-spoke source recognizer (native verified)

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
[Focused native CI #41883904480](https://github.com/joeyst8/witnora-core/actions/runs/41883904480)
passed Rust library tests, the compiled native wheel, and all focused
Python/Rust differential suites including R-071. The module is therefore
`parallel_reference`, taking the verified source count to **49/560**.
Existing Lean theorem provenance is independent of these software tests.
