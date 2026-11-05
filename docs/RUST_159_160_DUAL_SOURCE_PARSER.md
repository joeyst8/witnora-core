# R-159/R-160: optional dual Python/native original-CNF parser gate

`require_dual_source_parser=True` requires the R-157 identity gate and uses
the original Python DIMACS parser plus the established native Rust DIMACS
evidence parser over the same text.

- **R-159** compares canonical clause semantics after both independent
  parsers have processed exactly the same source text, including a canonical
  generated DIMACS fallback when no explicit text is supplied.
- **R-160** rejects any parser failure or disagreement before the proof
  checkers are invoked. A deliberate native-parser disagreement test confirms
  that neither internal RUP nor external `drat-trim` can be bypassed.

This is an opt-in cross-check on source interpretation, not a proof of byte
identity, parser formal verification, or equivalence for arbitrary invalid
input. Default exporter behavior and all downstream external proof checks are
unchanged.

**Status: implemented, native CI pending.**
