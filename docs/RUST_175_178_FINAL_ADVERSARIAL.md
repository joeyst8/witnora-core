# R-175–R-178: bounded final adversarial validation

- **R-175:** 70 new seed-relabeled, complete contradictory 1–3 XOR-gadget
  sources with exact Rust/Python proof output and original-CNF RUP validation.
- **R-176:** clause-count and byte-cap boundary rejection on width 1–3
  contradiction cases, compared to the Python reference.
- **R-177:** integrated row-trace corruption controls for missing parents,
  wrong parity, wrong support and absent result ID. The native proof candidate
  must fail closed and match Python's exact error category.
- **R-178:** remove each original source witness clause in turn; the native
  exporter must refuse proof generation with the source-clause-missing error.

These tests do not equate a finite RUP subset check with a general DRAT
verifier. They use bounded 1–3 XOR gadgets and leave external `drat-trim`
and Lean trust obligations intact. The Python implementation remains default.

**Status: held-out CI pending.**
