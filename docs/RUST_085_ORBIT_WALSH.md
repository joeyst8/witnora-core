# R-085: bounded orbit-Walsh identity as a Rust defect specialization

The near-complete coherent uniform-hypergraph orbit oracle is implemented in
Rust by restricting the already verified R-082 native defect-Walsh kernel to
at most `min(rank, max_missing)` missing rank-r clauses. With at most r missing
rank-r supports, no higher-than-r flip clique exists, because every (r+1)-set
would require r+1 missing clauses. This preserves the orbit formula without
duplicating its structural enumeration.

The optional Python `backend="rust"` is covered by 140 seeded coherent rank-2
and rank-3 source comparisons, free variable boundaries, empty source cases and
missing-clause limits. Python remains the default baseline. This is a standard
combinatorial identity, not evidence of a new SAT algorithm or a Lean proof.

Verified: **focused Rust CI #41917607815 passed** native library compilation,
the Python wheel and all focused differential suites. R-085 is marked
`parallel_reference` in the migration manifest.
