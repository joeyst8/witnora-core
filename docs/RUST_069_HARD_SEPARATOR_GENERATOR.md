# R-069 — Seeded planted hard-separator CNF generator (pending CI)

The single public generator in `hard_separator_families.py` now has an opt-in
native Rust assembly path. Python preserves the exact `Random(seed)` stream,
including 3-variable samples, random literal signs and the forced positive
literal when all sampled signs are negative. Rust independently builds the
canonical XOR boundaries, checks sampled local 3-CNF rows, and canonicalizes
the complete source formula.

The native differential gate covers all 12 preregistered `(blocks,core_vars,
width)` combinations across 8 deterministic seeds each: **96 exact
source-CNF hashes, complete clause lists and metadata records**, plus the
all-true planted satisfying assignment and invalid-grid rejection.

Until GitHub native CI passes, this is a pending parallel source module,
not a verified additional file. The planted witness establishes SAT for
those constructed instances; the word “hard” in the experiment name is
not a proof of computational hardness or a complexity-theory result.
