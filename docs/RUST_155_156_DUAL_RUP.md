# R-155/R-156: optional dual internal RUP-subset replay

- **R-155** adds `require_dual_internal=True` to the experimental XOR proof
  exporter. It runs the original Python RUP-subset checker and the existing
  independently implemented native Rust RUP subset checker over exactly the
  same original CNF and candidate proof.
- **R-156** compares their five semantic result fields and fails closed if
  they disagree. Even when both return verified, the independent external
  `drat-trim` verification must still succeed before a DRAT claim is promoted.

Two deterministic negative-gate tests check both elimination strategies with
a simulated unavailable external checker, and inject a deliberate checker
disagreement to assert that external verification is never entered after
internal divergence. The test mock is deliberately not proof evidence.

The default is unchanged: `require_dual_internal=False` preserves the Python
internal check and the mandatory external checker. Native RUP replay is a
secondary empirical implementation, not a Lean trusted kernel and not a full
RAT/DRAT verifier.

**Status: implementation pending CI.**
