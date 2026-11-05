# R-149/R-150: native bounded XOR parent-row resolution

- **R-149** ports the resolution closure for deriving one XOR row encoding
  from the two parent encodings, with the exact shared-variable elimination
  order, canonical non-tautological resolvents and deterministic clause order.
- **R-150** performs the expected-encoding subset check and bounded proof-line
  emission, carrying actual clause count, byte count, width, active set and
  specific cap-failure reason back into the Python candidate generator.

The opt-in `backend="rust"` row-trace route uses the native component but the
default remains the Python reference. A 180-seed differential test compares
the full emitted line sequence, active set and statistics under randomized
proof-clause and byte budgets. Wall-clock races are excluded from exact tests;
the native path still checks its own wall-clock budget and can fail closed.

**Status:** implemented, native CI verification pending. A generated
resolution sequence is not automatically a valid DRAT proof. Independent
RUP, `drat-trim`, and Lean trust obligations remain unchanged.
