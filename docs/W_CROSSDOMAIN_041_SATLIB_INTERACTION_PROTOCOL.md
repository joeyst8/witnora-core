# W041 — Prospective new interactions on untouched published SATLIB holdout

## Why this is a distinct attempt

The fixed W040 three cheap geometry descriptors **failed** on the first 200 official SATLIB `uf20-91` formulas (relative MSE -1.27%, p=0.404). This failure is permanent evidence. The next attempt uses a **non-overlapping, previously unread 200-case slice** and a *frozen different feature set*, without retuning on W040's held-out outcomes. Commit design and code before evaluating W041.

## Published source and frozen selection

- Exact official archive: `https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/RND3SAT/uf20-91.tar.gz`. Expected gzip SHA256 **`be2835295e8500bb28f0314eba70bd0deaff1250b187260f7b6d0772bdf111a5`** from W040's publisher download.
- Sort all 1,000 `.cnf` archive members lexicographically by the complete original member name, preserve source clauses and order, and take *zero-based ranks 200–399*. First 200 (ranks 0–199) were W040 and must be disjoint. Source validation is unchanged strict `p cnf 20 91`, all 91 clauses of width exactly three, `%` allowed after source clauses.
- All are publisher-labeled SAT; independently verify each completed DPLL assignment. Preserve the original DIMACS per-member SHA256 and the exact clauses in raw output. The unchanged **2,000,000-clause-scan cap** applies. If **any** case reaches cap, report censoring and **do not fit or report the primary regression/permutation p**.

## New precommitted feature set

Use only these three invariant **source-only** interaction measurements. They are not the three W040 cheap features:

1. **Opposite-polarity clause overlap:** among distinct clause pairs sharing at least one variable, the fraction with a shared variable used in opposite polarity in the two clauses (W037's `polarity_conflict`).
2. **Exact bounded-width Walsh nonconstant L1 / mean:** from W033's exact degree-3 clause-violation expansion (W037's `walsh_l1_to_mean`); no assignment-space enumeration and no solver labels.
3. **Signed-triangle frustration ratio:** build `A_ij=(1/m) sum_{clauses containing i,j} sign_i sign_j`, zero diagonal. For each distinct triangle `i<j<k`, define `w=A_ij A_jk A_ki`. Report `sum_{w<0} |w| / sum |w|`, or zero if denominator is zero. The product is invariant under independent variable polarity flips, analogous to frustration in signed spin systems.

Test exact equivalence of the first two features to W037, and sign-flip/variable-permutation/clause-order invariance of all three. Freeze definitions without looking at the new source measurements.

## Prediction and performance test

- Same target as W040: `log1p(exact transparent DPLL source-clause scans)` on **identical n=20/m=91/SAT** original formulas. Baseline is training-fold mean target.
- Frozen 5-fold cross-validation with seed **410041**, ridge penalty **10** on within-fold standardized three feature slopes and zero penalty on intercept. No hyperparameter selection.
- Primary score is relative held-out MSE improvement vs mean-only. Record MAE, per-fold errors and feature-vs-DPLL wall costs.
- **499** complete three-vector feature permutations across the 200 fixed-size SAT instances, seed **410042**, with fixed folds and retraining; one-sided p=`(1+null>=observed)/500`.
- Always report negative results. A positive prediction association is still not a solver-speedup or evidence for novel complexity bounds; family-held-out external validation is still required.
