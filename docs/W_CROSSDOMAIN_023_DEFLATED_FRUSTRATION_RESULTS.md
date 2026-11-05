# W-CROSSDOMAIN-023: gauge-deflated frustration held-out result

Protocol: `docs/W_CROSSDOMAIN_023_DEFLATED_FRUSTRATION_PROTOCOL.md`.
Raw publisher-source SHA-256 hashes and solver/feature measurements:
`research/results/w023_external_deflated.json`.

## Verification

- Dedicated W023 run passed:
  https://github.com/joeyst8/witnora-core/actions/runs/42125294708.
- Rust unit tests, independent Python numerical replay, and variable
  gauge-flip invariance tests passed. All six source CNFs match the
  independently checked VLSAT-2 dimensions and literal universes.
- Pinned original Kissat release `rel-4.0.4`; the raw report records its
  resolved Git SHA. No completed solver verdict contradicts the publisher
  status. **No independent UNSAT proof artifact was checked**.

## Frozen previously unseen VLSAT-2 sources

The signed polarity-gauge vector g is the normalized variable-wise
positive-minus-negative occurrence count divided by sqrt(degree).
`gauge_frustration=1-||Bg||²` measures the leading gauge-mode energy
deficit. `deflated_rayleigh` estimates a Rayleigh quotient on the
subspace orthogonal to g using twelve projected power iterations.
This is not the exact second eigenvalue of B^T B.

| Instance | Publisher | Kissat verdict | Kissat (s) | Rust (ms) | Top Rayleigh | Deflated Rayleigh | Gauge frustration | Polarity conflict |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 798_17543 | UNSAT | UNSAT | 11.876 | 8.719 | 0.999999845 | 0.980232 | 0.0001283 | 0.039631 |
| 1022_14955 | UNSAT | UNSAT | 2.821 | 7.519 | 0.999999624 | 0.966089 | 0.0009770 | 0.060661 |
| 1134_26703 | UNSAT | TIMEOUT | >15 | 13.224 | 0.999999717 | 0.982983 | 0.0001382 | 0.034082 |
| 1155_42917 | UNSAT | UNSAT | 12.389 | 21.162 | 0.999999977 | 0.988042 | 0.0000302 | 0.024213 |
| 7452_334035 | SAT | TIMEOUT | >15 | 167.446 | 0.999999988 | 0.989797 | 0.0001251 | 0.020229 |
| 11130_1186888 | SAT | SAT | 1.683 | 589.357 | 0.9999999995 | 0.995591 | 0.00000829 | 0.008839 |

Kissat was allowed 15 seconds per source. TIMEOUT indicates censoring,
**not** a logical decision. Rust time includes parsing and both old
top-mode and new deflated spectral measurements, excluding disk file
read and JSON printing. One run per instance means timing estimates
are descriptive and do not quantify run-to-run variance.

## Two findings, one positive and one cautionary

1. **Numerical saturation removed:** The undeflated top-mode score
   remains effectively 1.0, while the projected residual spans
   0.966089--0.995591. The W023 geometry is therefore measurable on
   harder examples and obeys the expected gauge-invariance controls.
2. **No evidence of added information beyond polarity:** On these six
   points the spectral defect `1-deflated_rayleigh` is almost a linear
   rescaling of the cheap polarity-conflict fraction. Sample Pearson
   correlation of the two defects is **+0.9961**, and five of six have
   ratio `(1-deflated_rayleigh)/polarity_conflict` between **0.493 and
   0.505**. Thus this experiment does not establish a novel hardness
   feature. Strong correlation in a six-case non-random cohort is
   descriptive, with no generalizable inference.

The largest sampled formula incurred **589 ms** of Rust profiling
while bare Kissat found SAT in **1,683 ms**, an overhead around 35%
of its solver time. There is still **no solver acceleration**. Solving
time is confounded by size, satisfiability status, family, and four
completed decisions versus two censored outcomes.

## Literature and claim boundary

Gauge switching and spectral frustration are established signed-graph
ideas. See, for example, the original work on frustration and spectral
inequalities at
https://www.sciencedirect.com/science/article/pii/S0166218X16304073.
Our special clause-variable signed bipartite operator is an empirical
diagnostic, not a newly proved complexity invariant.

Next proposed falsification: hold polarity conflict *fixed* while
varying true CNF interaction topology, and compare frustration spectra
against cheap baseline predictors. Until then, W023's signal is best
treated as a more expensive proxy for existing statistics.

**W023 does not prove P=NP, a new theorem, a solver advantage, or even
a useful hardness predictor.**
