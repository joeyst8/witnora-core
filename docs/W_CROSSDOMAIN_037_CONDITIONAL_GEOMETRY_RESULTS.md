# W037 — Conditional geometry predicts modest search work on frozen tiny SAT set

## Frozen protocol and evidence

- Experiment plan fixed before evaluation: `docs/W_CROSSDOMAIN_037_CONDITIONAL_GEOMETRY_PROTOCOL.md`.
- GitHub Actions success: [42165609477](https://github.com/joeyst8/witnora-core/actions/runs/42165609477).
- Source code commit: `0dc4b9894e06829c9d3d016c4a632e857829c524`.
- Complete source-frozen original 200 five-variable 3-CNFs: W034 uncompressed SHA256 `261ca8144fc27799c6790012157c42986be37d0c0378f0dbdac7a98d8681a8c7`.
- Independently verified DPLL source-clause scans: W035 uncompressed SHA256 `4451e2c8621c85aeca47e1e330cb29023acfe0920b3ed1a249a67d808c280e1a`.
- All 200 feature vectors, sizes, out-of-fold predictions, 200 within-size permutation improvements and confidence-interval provenance are in `research/results/w037_stats_raw.json.gz` (compressed SHA256 `127c50544c80722b76f75f1b8d89f24c763be33d845d3b0c46c81ccf4456fa48`, decompressed SHA256 `a85512a0c561a2560ed8416bc330ea55de1b598f1b3fb7feb86743a14773cd95`).

## Statistical outcome (pre-registered model and size control)

Same five Boolean variables in **every** formula. Clause counts stratified into `12, 16, 20, 24, 32`, 40 formulas each; exact size indicators available to both models. Target: `log(1 + exact DPLL source-clause scans)`, not SAT labels. Model training/testing split uses frozen stratified five-fold CV seed 370037, ridge penalty 10 on the five structural coefficients only.

| Held-out metric | Clause-count-only baseline | Baseline + five geometry/Fourier features |
| --- | ---: | ---: |
| Mean squared error | **0.079698** | **0.072442** |
| Mean absolute error | 0.217984 | 0.213289 |
| Relative MSE reduction | — | **9.10%** |

- Within-size feature-vector permutation test: **p = 0.004975** (none of 200 permutations matched or exceeded the observed improvement; one-sided minimum possible with 200 is 1/201).
- Observed paired held-out squared-error reduction: **0.0072562**.
- Frozen 2,000-draw within-stratum case-bootstrap 95% interval for *fixed fitted-model paired error reduction*: **0.0003023 to 0.0140685**. Models were not refitted in the bootstrap, and this should not be treated as a population-wide inference.
- Held-out MSE improved in the 12-, 16-, 20-, and 24-clause groups, but **worsened** in the 32-clause group (0.02210 baseline versus 0.02520 enhanced). The effect is not uniform.

The five predictors were normalized signed-literal imbalance, variable overlap between clauses, opposed-polarity overlap (frustration), exact Walsh nonconstant L1 ratio, and signed variable-interaction graph spectral radius. Tests confirmed invariance under renaming Boolean variables, simultaneous variable polarity flip and source clause reordering. Features depend only on the original formula, never on the SAT/UNSAT truth or solver work.

## Cost barrier and scope

- Median feature extraction wall time was **0.280606 ms** per formula on the W037 Python/NumPy runner.
- W035's archived median DPLL wall time on the same source cases was **0.056732 ms** per case. These values came from separate GitHub Actions runs and are **not matched end-to-end timing pairs**; nevertheless, they warn that measurement may dominate solving for tiny cases.
- Therefore the modest statistically positive *predictive* result is **not an algorithmic solver speedup**, a source UNSAT certificate, or evidence of polynomial-time SAT solving.
- The sample is restricted to **synthetic five-variable formulas** and a particular reference DPLL implementation. The 200 formulas are not statistically independent of the synthetic generation procedure; external/held-out family replication is essential.

## Next step

W038 should test these features (and cheaper approximations thereof) on larger **independent published SAT families**, with source hash verification, a true fixed extraction budget, and hold-out by *source family* rather than only formula instance. Estimate predictive value after controlling for variables, clauses, and SAT label stratification if appropriate; compare to established SATzilla/Hutter-style features. Do not deploy a gate unless the predictive value exceeds its exact feature and routing costs.

This is a limited result about conditional information in search cost, not a theorem about complexity classes.
