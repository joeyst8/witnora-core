# R-079: geometry-aware sparse parity native comparison

The `geometry_aware_parity` Python reference remains default. The Rust
counterpart constructs source primal edges, greedily groups variable-incident
3-CNF clauses into width-bounded buckets with identical fill scoring and tie
breaking, repairs duplicate column signatures, then compacts the parity rows.

The Python bridge still verifies each produced `SparseOddSketch` through the
existing source-bound validator. The focused differential suite covers 180
seeded exact-width-three CNFs, width 1..6, duplicate signatures and invalid
source geometry. This builds sparse parity candidates; it does not establish a
SAT speedup, guarantee optimal fill, or change Lean's trust boundary.

Verified: **focused Rust CI #41910107259 passed** library tests, native wheel
build and all focused Python/Rust source differential comparisons. The manifest
now records R-079 as `parallel_reference`.
