# R-145/R-146: validate parent IDs and XOR row operations

The bounded native validator checks two distinct obligations:

1. **R-145:** both named parent rows must exist in the current row-value map.
2. **R-146:** the proposed row's variable support must equal the symmetric
   difference of the two parents and its parity must equal their XOR.

The native function returns the same exact error category as the Python
reference. The optional `backend="rust"` on the row-trace candidate path
uses the already prepared native row sources and this validator, but the
subsequent clause derivation and final independent proof checks are unchanged.

The differential suite contains 420 fixed-seed random controls and explicit
valid, missing-parent, wrong-support, and wrong-parity cases. Native Rust
unit checks also exercise those cases independently.

**Status:** implemented, pending green native CI. This rejects malformed
trace metadata; it cannot alone establish the RUP validity of a resolution
clause, the soundness of a full DRAT proof, or any Lean theorem.
