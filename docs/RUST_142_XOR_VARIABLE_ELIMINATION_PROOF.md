# R-142: native bounded XOR variable-elimination proof candidate

The `xor_ve_refutation` Rust module now implements the complete deterministic
resolution-based proof candidate generation used by the Gaussian XOR DRAT
bridge. It preserves the source-support subset check, canonical clause
ordering, pivot elimination, tautology rejection, duplicate resolvents,
byte and clause limits, empty-clause termination and timeout checks.

`_variable_elimination_refutation(..., backend="rust")` exposes the native
candidate without changing the default Python reference path. Differential
tests compare the entire generated DRAT text, all error reasons and proof
statistics on seeded formulas, cap cases, contradictory units and empty
sources. Runtime-dependent timeout races are intentionally excluded from
exact-match tests.

**Trust boundary:** Rust generates a *candidate proof*, not an assertion that
the formula is unsatisfiable. The independent internal RUP subset checker,
external `drat-trim` and Lean verification conditions remain separate and
mandatory wherever the existing workflow requires them.
