# R-077 — Finite auxiliary violation bridge (pending native CI)

Native Rust computes literal-level source violation masks, local
clause/auxiliary factor scopes, direct parity factor scopes, bounded
exhaustive source model counts and the exact auxiliary violation weight
polynomial coefficients. Python retains its original source and sparse-sketch
validators and the public `AuxBridgeProfile` record, and remains the default.

The focused differential gate covers 120 seeded 3-CNF sketches, all finite
assignments (up to 7 source variables), scope equality, full coefficient
equality and fail-closed bounds. The exponential oracle remains restricted
to at most 14 variables: this is not a practical general tensor contraction
algorithm, formal proof, or a novel SAT technique.
