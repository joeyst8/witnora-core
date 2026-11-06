# W037 — Held-out size-conditioned geometry and Fourier runtime prediction

**Status at freeze:** proposed exploratory pilot; no outcome measured yet.

## Motivating question

Can geometric, frequency/Fourier, statistical-physics-style measures of how source constraints interact predict actual SAT search work **independently of instance size**, after controlling the variables and clause count? Prior W031/W036 results show predictive structure without a low-cost proven shortcut; W037 deliberately treats any structural score as *predictive information*, not an UNSAT certificate.

## Frozen data and size control

Use the exact **200 original 5-variable 3-CNFs** and 1,200 same-host DPLL invocations from W034/W035. The source CNF SHA256 is frozen by W034, and every DPLL clause count is replay-verified by W035. Each formula has exactly 5 variables and one of five clause-count strata `12, 16, 20, 24, 32` with 40 formulas per stratum. Outcome `y=ln(1+number of DPLL source-clause scans)` is independent of features; a SAT label is **not** an input feature.

## Exactly five preregistered structural features

1. `degree_imbalance`: sum over variables of `|positive−negative|`, divided by all literal occurrences.
2. `pair_overlap`: average shared-variable count between distinct source-clause pairs, normalized by 3.
3. `polarity_conflict`: among overlapping clause pairs, the fraction with at least one shared variable of opposite polarity.
4. `walsh_l1_to_mean`: exact W033 nonconstant Walsh L1 coefficient sum divided by constant coefficient, with no SAT oracle, LP, or optimization.
5. `signed_interaction_spectral_radius`: largest absolute eigenvalue of the normalized signed variable–variable co-occurrence matrix. This is a signed graph statistic, not a physical frequency source or evidence of P=NP.

All five must be invariant (up to floating error for eigenvalues) under relabeling variables, consistently flipping one Boolean variable, and clause permutation. Add tests before launching the experiment.

## Freeze statistical evaluation before outcomes

- Deterministic **5-fold CV stratified by the five clause counts**, seeded `370037`: within each stratum shuffle 40 rows, assign folds in round-robin order. No train/test mixing for a formula.
- Baseline: five one-hot clause-count indicators. Enhanced: identical indicators **plus all five features** standardized using *only the training fold*. No SAT label, target, or test information enters the feature calculations.
- Fit one fixed ridge model with penalty `λ=10` on the five standardized feature coefficients and zero ridge penalty on the five baseline clause-count indicators. Hyperparameters are not selected using test outcomes.
- Primary: relative reduction in held-out MSE of `log1p(DPLL clause scans)` from baseline to enhanced model. Report MAE, per-stratum errors and raw held-out predictions too.
- Negative control: 200 independent, seed-fixed **within-clause-count feature-vector permutations**; recompute enhanced CV each time with labels and folds unchanged. One-sided p-value `(1+#null_improvement >= observed)/(201)`.
- Stability: 2,000 fixed-seed stratified case bootstraps of paired baseline-vs-enhanced held-out squared-error differences, with a transparent caveat that the fitted models are not refitted in each bootstrap.
- **Cost accounting:** time feature extraction per formula on the same machine and compare those costs with the W035 DPLL scan count/timing scale; a statistically predictive feature is not automatically economical to compute.

## Decision rule and caveats

Call it evidence for *conditional predictive value on this very small distribution* only if out-of-fold MSE improves and the within-size permutation p-value is below 0.05. Otherwise report the negative finding. Even a positive result would need new independent non-synthetic SAT families and cost-inclusive deployment testing before any performance or research novelty claim.

SAT runtime prediction, feature-based solver selection and structural analysis have substantial prior art: Xu et al., *SATzilla* (2008), https://doi.org/10.1613/JAIR.2490; Hutter et al., *Algorithm Runtime Prediction: Methods and Evaluation* (2014), https://arxiv.org/abs/1211.0906; statistical-mechanics phase-transition research such as Kirkpatrick and Selman (1994), https://pubmed.ncbi.nlm.nih.gov/17780846/. Our specific feature combination is a testable hypothesis, not a claim of mathematical discovery.
