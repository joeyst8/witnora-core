# W-CRC-012: End-to-end bounded cutset #SAT versus independent Ganak

Status: **pilot proof of concept with restricted-family wins, not
a general-purpose #SAT/SAT result**.

Verified post-fix green GitHub Actions (**79 Python tests**):
https://github.com/joeyst8/witnora-core/actions/runs/41718161372

## The actual end-to-end question

If Witnora must **automatically discover** a small source-primal
separator before counting, can the cost of cut discovery be recovered
by independently counting the resulting components?

For two simple families, **yes in this pilot**. This is the first
experiment in this series timing a complete model counter rather than
a certificate alone.

## Exact method

`witnora_core/crc_cutset_count.py` performs:

1. Validate an offered *full signed-source satisfying assignment*,
   automatically find a minimum primal-graph vertex cut between
   declared source groups using W-CRC-011, and verify its conditional
   graph certificate with W-CRC-010.
2. Enumerate **every** assignment to the found separator, not just
   the branch selected by the offered witness.
3. Partially evaluate each original signed source clause under that
   assignment. Reject contradictory/empty-clause branches as zero.
4. Union the variables in each surviving clause into residual
   disjoint primal components; free variables are included.
5. Exhaustively count each *small* non-free component using local
   Boolean assignments; multiply disjoint component counts, sum all
   separator branches, and return an exact nonnegative Python int.

Every output is exact under its source/witness contract. The method
returns `None` rather than an approximate or wrong count when cut
discovery fails, a component exceeds its size budget, separator branch
count exceeds 64 (configurable hard maximum 256), or the global
enumerated-assignment state budget is exhausted.

The time complexity remains exponential in separator size and largest
residual component size. This is standard cutset conditioning, not a
new polynomial-time general #SAT algorithm. The API requires a
**preexisting SAT witness**. Searching for one is not timed here, and
this limits the practical end-to-end interpretation.

## Independent correctness controls

- Six new W-CRC-012 tests cover exact star formulas, a signed XOR
  equivalence chain, disconnected source components, two-variable
  separators, infeasible separator branches, forged witness and
  budget failure, and **120 seeded small random source formulas**.
- For every admitted small random formula, a separate exhaustive
  full-assignment #SAT evaluator checks the integer result.
- Eight larger benchmark cases were checked against **Ganak** and
  separately against exact closed-form model counts.
- GitHub Actions run #41718161372 passed **79 Python tests**,
  including the added W-CRC-011 oversized-budget regression.

A fresh W-CRC-012 test originally uncovered a preexisting W-CRC-011
corner case: terminal/infinite capacity was n+1 but could be less
than a user-specified max cut budget. The fix sets capacity above
both n and that budget. The failing direct-edge case now returns
`None` rather than raising a min-cut extraction invariant.

## Benchmark families

**1 hub:** n-1 clauses `(x_i ∨ h)`.
- When h=1 all non-hub variables are free.
- When h=0 all non-hub variables are forced to 1.
- Exact count: `2^(n-1) + 1`.

**2 hubs:** two clauses `(x_i ∨ h1)` and `(x_i ∨ h2)`
per non-hub variable.
- When both hubs are 1, all non-hubs are free.
- In the other three hub assignments, every non-hub is forced to 1.
- Exact count: `2^(n-2) + 3`.

These are highly symmetric easy decompositions chosen to check the
architecture, **not representative random SAT problems**.

## Measured result (same GitHub Actions run)

Median of 2 complete Python W-CRC invocations; Ganak independent
counter in a child process. Ganak's **engine time excludes process
startup**; W-CRC time includes cut discovery, all branches and local
counting. Ratios below use engine time and are pilot measurements.

| n | Hubs | W-CRC full ms | Ganak engine ms | W-CRC / Ganak | Both exact? |
|---:|---:|---:|---:|---:|---|
| 16 | 1 | 0.3075 | 9.4233 | 0.033 | yes |
| 16 | 2 | 1.0431 | 11.4803 | 0.091 | yes |
| 64 | 1 | 0.8337 | 26.7434 | 0.031 | yes |
| 64 | 2 | 1.5810 | 30.7380 | 0.051 | yes |
| 128 | 1 | 1.5057 | 47.7223 | 0.032 | yes |
| 128 | 2 | 2.9698 | 47.7585 | 0.062 | yes |
| 256 | 1 | 2.8782 | 80.4247 | 0.036 | yes |
| 256 | 2 | 6.0209 | 101.2248 | 0.059 | yes |

This is roughly **11–32× lower measured wall time** for W-CRC in
these eight controlled instances. All 8/8 Ganak model counts
matched the exact analytical formulas and W-CRC integers.
Ganak's wrapper reports its default probabilistic-cache setting;
agreement with analytic integer formulas supplies an independent
mathematical control on this benchmark.

The maximum value counted was astronomical (for one hub at n=256,
`2^255+1`), demonstrating compact component counting, not actual
explicit enumeration of those models.

## Critical limitations

- Obtaining the offered SAT witness is external to the timed method.
  These benchmark inputs use a trivial all-ones witness.
- Endpoints A/B must be declared; automatic optimal pair/group
  selection is not implemented.
- The solver is incomplete by design on instances without a small
  graph cut or with large residual connected components.
- The models favor component decomposition; competitive general #SAT
  solvers have their own preprocessing and heuristics, and multiple
  benchmark families and seeds are required before general rankings.
- The measurements use very short runtimes and two repeats. No
  confidence interval or statistically robust solver ranking exists.
- The algorithm implements familiar graph decomposition and local
  enumeration. These results neither prove P≠NP nor suggest a
  general polynomial-time SAT solver.

## Next falsification target: W-CRC-013

Test heterogeneous and adversarial instances where:
1. the min-cut is present but a residual component exceeds budget;
2. no small vertex cut separates chosen endpoints;
3. model-count comparisons to Ganak are made for unsymmetric chains,
   small tree-like components and random controls;
4. source-witness acquisition cost is explicitly visible where
   feasible. Report all `None` admissions and failures, not just
   successful structured cases.
