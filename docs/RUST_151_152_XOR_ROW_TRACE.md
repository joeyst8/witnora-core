# R-151/R-152: native XOR row-trace candidate assembly

This opt-in native function consumes a deterministic normalized row-operation
trace, original clauses, and detected source-XOR witnesses. It checks source
subset identity, parent-row existence, GF(2) support/parity, bounded clausal
resolution, result-row availability and contradiction termination. It returns
the exact candidate DRAT text plus failure reason and resource accounting.

The existing Python row trace remains the default. A 140-seed differential
suite compares both candidates, including malformed-parent and tampered-parity
operations, randomized clause/byte caps, and explicit contradictory-unit and
missing-source cases. Runtime-dependent timeout races are not asserted to
match; both paths fail closed under their own deadline.

The native gadget builder has an explicit 16-variable cap. Widths above that
cap cannot be promoted as verified matches without a separate admission gate.

**Status: implemented, native CI pending.** Source-to-proof output is not an
independent verification. The RUP checker, external `drat-trim` and Lean
trust criteria remain unchanged.
