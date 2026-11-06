# W038 — Frozen independent 8-variable cheap-geometry replication

## Status before outcome

**Prospective design; freeze this file and the benchmark program in a GitHub commit before running the evaluation.** W037's three-feature subset was selected *after* inspecting W037's 200 five-variable synthetic formulas, and its apparent 10.06% held-out MSE improvement on those same formulas is exploratory and selection-biased. W038 must use a new independently seeded source generator, without looking at its performance to change features, lambda, sample sizes, or splits.

## Hypothesis

The three source-only features (signed degree imbalance, exact pair overlap, signed interaction graph spectral radius) predict DPLL log clause-scan cost after conditioning on clause count in a new, uniform random eight-variable 3-CNF family. Test against a clause-count-only baseline. Exact W037 five-feature method is a secondary comparator; no feature selection is permitted after the W038 run.

## Frozen sample and modeling

- **200 formulas**, eight variables each, 40 at each of 24/32/40/48/56 clauses.
- Generate all 448 non-tautological distinct 3-variable clauses by choosing three of eight variables and one of eight polarity assignments. Use `random.Random(380038).sample(all_clauses,m)` without replacement, 40 successive draws per size stratum. The sampled clause order is part of the source and affects the deterministic reference DPLL. No planted witness, no solver knowledge, no label-based sampling.
- Use reference Python DPLL exact original-clause scans as the target, transformed as `log1p(scans)`. Never put SAT/UNSAT label, scan count, or branch tree into feature extraction. Retain labels in raw results for transparency.
- Freeze fivefold size-stratified CV with `random.Random(380039)` and assigning fold `position % 5` after independent shuffle of each size stratum. Baseline = five clause-count indicators. Enhanced regressions = same indicators plus the three features, or all five W037 features; within-fold standardization, ridge λ=10 on structural slopes and no penalty on size intercepts.
- Predeclared primary measure is relative held-out MSE improvement of the cheap-three model over size-only. Report held-out MAE, per-stratum MSE, and the all-five comparator descriptively. For cheap-three only, use **200** full-feature-vector permutations *within each size stratum* with seed 380040, evaluating fixed folds, and `(1 + #null >= observed)/201` as a descriptive permutation p-value. The minimum possible is 0.004975.
- Run cheap-three, all-five, and DPLL within the same CI process and capture per-instance wall-clock nanoseconds, while noting Python timing caveats. Report median cheap-feature time divided by median DPLL time, but do not call it a deployment speedup.

## Correctness and interpretations

The cheap pair-overlap metric must be mathematically identical to W037's quadratic clause-pair implementation. It uses the incidence identity `sum_v choose(deg(v),2) / [3 choose(m,2)]`; the signed spectral feature must match the original eigenvalue computation. Tests must check exact feature agreement, variable renaming, sign flips and clause order invariance.

Any failure to replicate is recorded unchanged. Passing association cannot establish SAT/UNSAT correctness, accelerated solving, or generalization to external industrial source families. The test changes both formula variable count and generation mechanism, but remains synthetic; subsequent family-level published benchmark replication remains necessary.
