# R-143/R-144: native XOR source-row preparation

Two bounded migration steps extend the Python-to-Rust comparison surface:

- **R-143** creates deterministic `input_####` row IDs and deduplicated source
  clause sets, matching Python's `_source_row_encodings` output.
- **R-144** preserves source equation variable supports and parity bits, matching
  `_source_row_values` output.

The optional `backend="rust"` calls are differential entry points; the Python
reference remains the default. The 180-seed regression compares both full
maps, including zero rows, empty clauses, duplicates and varying source order.
The native Rust unit test covers canonicalization and row naming separately.

**Verification status:** implemented, pending full native Rust CI. This is
data preparation, not a DRAT proof, a RUP check, a Lean theorem, or a claim
that the row-trace refutation generator has been migrated.
