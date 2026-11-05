# R-147/R-148: XOR result encoding and source-clause union

- **R-147** threads the already native exact canonical XOR-CNF gadget encoder
  into the opt-in row-trace candidate path. It compares 200 seeded random
  small parity gadgets to the Python encoding, including empty supports.
- **R-148** adds native deduplicated union of the original source-CNF clauses
  supporting detected XOR rows, compared against the Python source collector
  on 250 seeded controls. It is exercised before attempting row derivation.

The Python path stays default. Native width caps are intentionally fail-closed;
the tests use small bounded gadgets where both backends must agree. Neither
step proves that the row operation's emitted clauses are RUP, and neither
weakens the independent DRAT/Lean verification boundary.

**Status:** implementation pending CI verification.
