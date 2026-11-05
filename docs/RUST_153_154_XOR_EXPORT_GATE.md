# R-153/R-154: optional native XOR proof exporter with unchanged trust gate

The public XOR-to-DRAT exporter now accepts `proof_backend="rust"` explicitly;
the default remains the Python reference. The same argument routes either
Gaussian variable-elimination candidate generation or sparse-min-fill row
trace candidate generation to their native implementations.

**R-153** threads the opt-in backend selection through the full exporter;
unknown values raise an error. **R-154** asserts that both Python and Rust
candidates still enter the existing independent internal DRAT/RUP subset
checker and external `drat-trim` verifier before any verified status can be
reported. A mocked unavailable external checker in the regression test must
yield a non-verified result for both elimination strategies.

No external verifier is replaced by Rust code. The negative-checker test is a
trust-gate wiring check, not evidence of externally verified DRAT. The default
behavior, Lean obligations, and signed source-CNF identity remain unchanged.

**Status:** implemented, native CI pending.
