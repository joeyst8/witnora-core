# W034 — Nonnegative weighted spectral certificate, exact audit

## Question

Does optimizing nonnegative clause weights rescue W033's global Fourier lower bound when unrelated clauses drown out local source contradictions?

**No novelty or P=NP claim.** This is a constrained LP proof search that may reproduce known linear programming, MaxSAT dual, or Fourier relaxation techniques. The numerical optimizer is a *candidate generator*, not a proof authority.

## Soundness, integer certification, and LP formulation

For nonnegative weights `w_c`, let `E_w(x)=Σ_c w_c I_c(x)`. Every satisfying assignment of the original formula has `E_w(x)=0`. Collect Fourier integer coefficients `b_S(w)` by linearity. For every assignment,

`E_w(x) >= [b_empty(w) − Σ_(S≠empty)|b_S(w)|] / 8` for clauses of width ≤3.

If this bound is strictly positive **and weights are checked to be nonnegative**, the original formula is UNSAT. The proof is exactly checkable using **source clauses and integer arithmetic**, even if the LP optimizer produced floating values.

Search for `w_c >= 0`, `Σ w_c = 1` and nonnegative auxiliary `t_S` minimizing `Σ_S t_S − b_empty(w)` under `t_S >= ±b_S(w)`. Solve with SciPy HiGHS, then round proposed weights to nonnegative integers at a fixed scale of `1,000,000` and **recompute all coefficients with Python integers**. Only an integer lower bound strictly above zero is ever accepted. A floating-point LP gain without a positive audited integer lower bound yields `NO_CERTIFICATE`.

With maximum clause width three, the sparse support count is polynomial in source size, but LP cost and candidate number can be substantial. No claim about arbitrary CNFs or favorable scaling.

## Frozen exploratory small-formula study

- `n=5` Boolean variables; all **80 possible distinct non-tautological 3-clauses** as source pool.
- Fixed pseudorandom seed `340034` for Python `random.Random`.
- For each clause count `12, 16, 20, 24, 32`, take 40 without-replacement 3-CNF samples sequentially from that generator; **200 total source formulas**.
- Determine SAT/UNSAT independently by enumerating all **32 Boolean assignments** per case.
- Run both W033 unweighted spectral test and W034 nonnegative weighted LP. Retain exact source formulas and exact proposed integer weights, optimization duration and lower bound for each case; all cases independently verified.
- Explicit examples: one UNSAT 8-pattern cube with two irrelevant 3-clauses where W033 fails yet W034 recovers the certificate; one frozen UNSAT 16-clause 3-CNF where **W034 fails**, demonstrating incompleteness.
- Collect per-stratum certificate counts, false-positive count, median numerical LP wall time. These are a **small exploratory dataset**, not a generalization claim; any selection or post-hoc subset must be identified.
- Do not compare Python LP time directly to Rust or a C solver without running cost-inclusive common-hardware benchmarks. Use large independent source families only after cheap preselection is identified.

## Relationships to earlier work

- W032: Rust XOR precheck found zero proof on eight external VLSAT2 CNFs.
- W033: unweighted Walsh L1 bound found zero external proof; added unrelated source clauses can weaken the bound.
- W034 tests whether sparse nonnegative weights restore a valid local proof while preserving exact source-level verification.

It would be mathematically incorrect to claim that this LP certificate resolves P versus NP or that all unsatisfiable 3-SAT formulas admit one. A frozen explicit unsatisfiable counterexample in `tests/test_w034_weighted_walsh.py` shows the proposed relaxation is incomplete even at five variables.
