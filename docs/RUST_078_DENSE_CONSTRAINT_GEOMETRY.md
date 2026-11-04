# R-078: dense constraint geometry native differential gate

`witnora_core/constraint_geometry.py` keeps the Python reference as its default.
The optional `backend="rust"` now covers independent dense parity row
assembly from frozen Python `getrandbits` draws, bound source/row validation,
exhaustive small-source collision profiles, singleton coverage bounds and row
statistics. Native Rust processes arbitrary-width clause bitmaps via `BigUint`.

Randomness is generated outside Rust to preserve Python's seeded MT19937 stream
and `SystemRandom` semantics. The row builder is nonenumerative; the collision
audit explicitly enumerates assignments and is restricted to small examples.
Neither gives a polynomial-time SAT algorithm or a Lean proof.

The focused CI gate runs `tests/test_constraint_geometry_rust.py` (120 seeded
source/sketch comparisons, 201-clause bitmap, invalid sketches) alongside prior
Rust source-differential suites. Status stays unverified until CI succeeds.
