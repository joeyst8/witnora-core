# R-138–R-141: XOR DRAT encoding and bounded emission helpers

- **R-138:** `_xor_encoding_clauses(..., backend="rust")` uses the
  previously verified exact native XOR-to-CNF encoder, including empty
  parity constraints, duplicate variables, and signed parity.
- **R-139:** `_clause_line(..., backend="rust")` formats a clause for DRAT,
  preserving literal order and the terminating zero.
- **R-140:** `_line_size(..., backend="rust")` counts exact output bytes,
  including the newline, for proof budget accounting.
- **R-141:** `_emit_clause(..., backend="rust")` uses a native decision
  for deduplication, width tracking, clause caps and byte caps. Python
  appends the emitted line and mutates the clause set only when allowed.

The focused workflow checks 180 seeded encodings, 200 formatted lines,
200 byte lengths, and 250 emitted-clause state transitions against the
reference implementation. These milestones do not replace the separate
proof-checking step: output clauses still require a correct DRAT/RUP
checker, and Lean verification has not been weakened or bypassed.
