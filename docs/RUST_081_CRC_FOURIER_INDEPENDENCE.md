# R-081: exact CRC Fourier cross-moment native audit

The `crc_independence_audit` module now supports `backend="rust"` for exhaustive
left/right Fourier-mode generation and exact cross-moment independence testing.
Arbitrary-precision mode masks and signed fractional coefficients are passed as
decimal strings, so no floating-point approximation or 64-bit cap enters the
native comparison. The source-defect Walsh oracle and source normalization
remain in their existing independently checked Python modules.

The focused regression runs 120 seeded supported near-complete signed sources,
positive and negative independence cases, and high-bit exact-fraction controls.
The Python reference remains the default. This is not general SAT independence
or a Lean proof.

Status: awaiting compiled Rust CI verification.
