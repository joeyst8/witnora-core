# W-CROSSDOMAIN-023: gauge-aware deflated spectral frustration

Status: **prospective protocol frozen before W023 held-out measurements**.
Upstream W022 report: `docs/W_CROSSDOMAIN_022_REAL_WORLD_SPECTRAL_PILOT_RESULTS.md`.

## Motivation and boundaries

The W022 normalized signed incidence operator `T=B^T B` produced
Rayleigh values in `[0.99998573, 0.99999999]` on eight VLSAT-2
benchmarks. For single-polarity variables its eigenvalue 1 is forced
by simple normalization; thus the leading mode can obscure the
frustration created by opposing signs. In signed-graph theory,
switching/gauge equivalence and frustration spectral bounds are
existing mathematics, **not inventions claimed by Witnora**.

Question: does removing the *polarity-imbalance gauge mode* reveal a
non-saturated, low-cost feature on independent real-world formulas?
This pilot does NOT implement a new solver or assert hardness prediction.

## Two predefined measures

For formula F use W022's normalized incidence matrix B and degrees d.
For variable v, let `h_v=(pos_v-neg_v)/sqrt(d_v)` (zero for `d_v=0`).
Normalize h to unit length to get g. If h is zero, output unavailable
for both gauge-derived measures instead of choosing an arbitrary gauge.

1. **Signed gauge frustration energy**:
   `frustration = 1 - ||B g||²`, clamped only for machine precision.
   If each variable has a consistent sign, frustration is identically
   zero. It need not imply UNSAT; it is a geometric energy, not proof.
2. **Deflated residual Rayleigh**: let `P=I-gg^T`. Iterate
   `x <- normalize(P T P x)` for **12** steps, starting with
   `x_v = g_v*((v mod 5)-2)` and project away g. If zero, retry
   `g_v*((v mod 7)-3)`; if still zero report unavailable. Report final
   `x^T T x` as a *finite-iteration estimate*, not the exact second
   eigenvalue. No adaptive tuning per source or post hoc thresholding.

Also report W022's top Rayleigh estimate, polarity conflict fraction,
variable count, clause count, runtime for the complete W023 extraction,
and the source's literal-occurrence count. Complexity is bounded by
O(12 * occurrences), with two `B^T B` passes per iteration plus the
old W022 eight passes. No dense eigen-decomposition.

Under a Boolean gauge transformation (flip all occurrences of any
variable) B has its variable column sign-flipped, and g transforms
by the same sign. Both proposed scalar features should be invariant
up to floating-point tolerance. Tests must check a nontrivial formula,
its single-variable gauge flips, and independent Python references.

## Frozen external held-out cohort

Do not use W022's eight source inputs to choose thresholds. Freeze six
other VLSAT-2 publisher sources:

| Stem | Publisher SAT status |
| --- | --- |
| `vlsat2_798_17543` | UNSAT |
| `vlsat2_1022_14955` | UNSAT |
| `vlsat2_1134_26703` | UNSAT |
| `vlsat2_1155_42917` | UNSAT |
| `vlsat2_7452_334035` | SAT |
| `vlsat2_11130_1186888` | SAT |

Sources hosted by INRIA at the original VLSAT-2 HTTPS location.
Record compressed and decompressed SHA-256 and strict DIMACS count
controls; do not silently substitute missing cases. Exact published
labels are independent of our profiling and Kissat timings.

## Baseline, controls and inferential limits

- Kissat `rel-4.0.4`, pinned to resolved upstream Git commit. Cap each
  solve at 15 seconds. Preserve SAT/UNSAT/timeout/error separately;
  a timeout is censored, not a decision.
- Independent tiny-formula controls compute the real B matrix and
  repeat both projected operations in Python (not by copying Rust
  output). Gauge-flipped variants must agree numerically.
- For the held-out cohort report all raw features and timers, compare
  spread to W022's saturated top mode, and check whether the proposed
  features are distinguishable from simple polarity conflict. Report
  *no* statistical significance or universal prediction from six
  nonrandom, label-imbalanced, size-confounded instances.
- Do not claim new SAT proof, acceleration, new spectral theorem or
  progress toward P=NP unless independently established.
