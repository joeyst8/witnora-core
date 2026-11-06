# W027 auxiliary statistical decision analysis

**Status:** analysis specification written while the full W027 CI run was
active, **before inspecting its full-run results**. It is therefore
exploratory and cannot retrospectively redefine the primary W027
performance decision rule or any frozen cases.

Suppose, for a fixed source-generating distribution, Witnora saves an
average of `g` milliseconds on UNSAT instances and adds an average
cost of `s` milliseconds on SAT instances, each measured over the full
pipeline. If the incoming UNSAT proportion is `p`, the expected
*Witnora-minus-Kissat* wall-time difference is

    E[delta] = (1 - p) * s - p * g.

For positive `s` and `g`, Witnora is faster in this artificial mixture
only when `p > s / (s + g)`. If a gain or a penalty has the opposite
sign, the script handles the piecewise inequality directly rather than
silently forcing the threshold into the 0–1 interval.

Analysis implementation: `scripts/analyze_w027_break_even.py`.

- Pair the SAT and UNSAT source formulas with the **same** noise size
  and replicate seed. Exclude a pair from uncensored timing estimates
  if either of its four relevant arm/case medians lacks three solved
  repetitions; preserve and report the excluded count.
- For each of the six noise levels, compute arithmetic *mean* full
  pipeline SAT penalty and UNSAT saving over up to 16 paired seeds.
  Means are used because the decision equation concerns expected time.
- To describe finite-sample variation, resample the **16 seed pairs**
  with replacement 5,000 times using fixed seed `0x02702700 + noise`,
  calculating the break-even threshold each time. Report conditional
  percentile intervals only when the ordinary `p > threshold` regime
  holds; never silently impute timeouts or claim these intervals account
  for between-distribution uncertainty.
- The control-generating source is deliberately biased toward obvious
  XOR contradictions. This analysis cannot estimate how often real SAT
  workloads are UNSAT or claim that the pipeline is faster in nature.

This is a connection between a constraint solver's algebraic
certificate and a statistical decision policy. It can inform future
prospective *routing* experiments, but routing thresholds must be set
using separate training data and evaluated on held-out distributions.
