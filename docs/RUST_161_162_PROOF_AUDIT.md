# R-161/R-162: independent native candidate text/statistics audit

- **R-161** adds a bounded native audit of emitted candidate proof text:
  each line must be a non-deletion clause of signed integers followed by
  `0`, and proof text must end with a newline. The independent audit returns
  actual clause count, maximum width and exact UTF-8 bytes.
- **R-162** adds `require_native_proof_audit=True` to the experimental exporter.
  The audit's count and byte total must equal the generator's claimed totals;
  emitted maximum width must not exceed its reported peak attempted width,
  otherwise processing stops **before** both the internal RUP checker and
  external `drat-trim`.

There are 240 seeded proof-text accounting comparisons, malformed syntax
controls and a deliberately tampered counter test. A successful audit still
cannot certify UNSAT, clause RUP validity, or DRAT soundness; those are checked
separately by the existing independent verification pipeline.

Default behavior is unchanged. **Status: implementation pending native CI.**
