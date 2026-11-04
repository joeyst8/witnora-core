# R-097: exact bounded k-colorability in Rust

The core backtracking decision/witness procedure now has an opt-in Rust
backend. It mirrors the Python DSATUR saturation-degree/vertex-ID tie breaks
and canonical new-color symmetry reduction. The associated chromatic
certificate and fixed adversarial experiment accept the same opt-in backend.
Sampling remains the frozen Python random stream for experimental parity.

Differential tests compare 360 seeded graph/k inputs, complete and path
families up to 16 vertices, full chromatic certificates and malformed cases.
The exhaustive decision procedure is exponential; this is an implementation
migration and supplies neither a complexity breakthrough nor a Lean theorem.

Status: Rust library compilation, native wheel and focused differential gate
passed in GitHub Actions #41932752484.
