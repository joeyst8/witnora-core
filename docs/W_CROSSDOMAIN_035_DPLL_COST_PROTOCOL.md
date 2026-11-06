# W035 — Cost audit against explicit exact DPLL

## Research question

W034's integer-audited weighted Fourier bound certified 74/77 small UNSAT formulas. But does its numerical search cost less than ordinary complete Boolean reasoning on those exact inputs?

## Frozen comparison

- Same 200 `n=5` source formulas, SHA256 protected and independently truth-table-classified in W034. No new training or cherry-picking.
- Two Python implementations running on the **same GitHub Actions machine**: (1) direct, transparent source-clause-scanning recursive DPLL with unit propagation, and (2) W034 SciPy HiGHS numerical candidate search followed by strict integer source-certificate auditing.
- Three complete repetitions per arm/case; rotate arms to mitigate order bias. Record 1,200 timed algorithm-only invocations, including every DPLL clause scan, propagated unit and decision.
- Check DPLL outcomes against every W034 truth-table label. Check W034 proof outcomes against the same archived frozen results.
- Primary metric: per-case median wall time W034 LP / DPLL; secondary: count of cases where W034 faster. The microsecond timings have Python/runtime noise and are **not** a production SAT benchmark.
- Reproducibility: archive each invocation and the original SHA-protected source dependency. Compare cost on the same host; do not use cross-run median ratios.

This small audit can *falsify practical advantage on tiny formulas*, but cannot establish or refute scaling to external industrial instances. Follow-up external evaluation must compare to production Kissat/CDCL and charge all preprocessing and proof costs.
