# R-157/R-158: optional original-CNF identity admission

The experimental exporter can now enable `require_source_identity=True`.

- **R-157** parses any explicitly supplied `original_dimacs_text` using the
  existing strict DIMACS parser and compares canonical clause sets with the
  `original_formula` object. Clause order, comments, tautologies removed by
  canonicalization and unused declared variables are not semantically
  significant for this source-formula equivalence check.
- **R-158** fails closed on malformed or semantically different source text
  **before** invoking either internal RUP checker or external `drat-trim`.
  A test checks this negative path, plus positive equivalence inputs where an
  unavailable external checker must still refuse a verified result.

This is a semantic-CNF match, not a byte-identical source archive proof. It
does not alter the default exporter or substitute for existing original-CNF
integrity hashes and Lean obligations. The check is opt-in until independent
CI and integration review establish suitability for default activation.

**Status: implemented, CI pending.**
