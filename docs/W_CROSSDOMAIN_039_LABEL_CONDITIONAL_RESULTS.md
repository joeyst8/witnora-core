# W039 — Conditional complexity signal largely vanishes with SAT status matched

## Frozen source and trusted replay

- **Precommitted design/code**: `docs/W_CROSSDOMAIN_039_LABEL_CONDITIONAL_PROTOCOL.md`, commit `a8278c99df3ee7a29eeb54206fd428e480312d63`. Outcome was not used to change the model, features, sample or folds.
- **Successful source generation and experiment**: [GitHub Actions 42170424022](https://github.com/joeyst8/witnora-core/actions/runs/42170424022); original artifact `w039-conditional-raw` ID `13480518598`.
- **180 independent synthetic ten-variable 3-CNFs**: exactly 30 SAT and 30 UNSAT for each clause count 38, 42, and 46. Generation used the separate exhaustive 1,024-bit truth-table oracle; random seed 390039; acceptance by label alone, never by reference DPLL work. The generator required 220, 130, and 67 source draws at the respective sizes.
- Archived every accepted source clause sequence, oracle label, source attempt number, reference DPLL scans, three feature values, fold, predictions, wall time and all 499 permutation values in `research/results/w039_conditional_raw.json.gz`.
- Compressed SHA256 **`8efad0b925540a807bb1cceb93d3892c72872a0952ce643585d4193e75684c6f`**, decompressed JSON SHA256 **`6595b74cb73cd8c6073f8baa2cbaa8cec9d494bb0c8f3079d4d87f149c9c5927`**.

## Primary preregistered question and negative result

Do the three W038 cheap geometric features add information about **`log1p(exact DPLL source-clause scans)`** when baseline comparisons already know the exact `(clause count, SAT/UNSAT)` stratum? This stricter test intentionally has an *unavailable ground-truth oracle* on both sides, to isolate conditional association rather than offer a deployable predictor.

| Held-out statistic | Six (clause count, SAT status) indicators | Indicators + three geometry features |
| --- | ---: | ---: |
| Mean squared error | **0.138103** | **0.137051** |
| Mean absolute error | 0.308025 | 0.305285 |
| Relative MSE improvement | — | **0.76%** |

- **Predeclared within-(size, status) permutation p = 0.112** across 499 permutations. This does **not** support a convincing conditional association at conventional significance thresholds. It is not proof the conditional effect equals zero.
- Same source data, secondary size-only comparison: MSE **0.209281 → 0.192774**, or **7.89%** improvement. Contrasting it with the 0.76% primary result reinforces the possibility that features are tracking satisfiability-related regimes. The secondary number is descriptive, not the preregistered primary inference.
- Improvement by six matched cells is **mixed**, not consistently directional:

| Cell | Baseline MSE | + Geometry MSE |
| --- | ---: | ---: |
| 38 clauses / SAT | 0.218481 | 0.210483 |
| 38 clauses / UNSAT | 0.121148 | 0.120122 |
| 42 clauses / SAT | 0.173428 | 0.163267 |
| 42 clauses / UNSAT | 0.048082 | **0.054308 (worse)** |
| 46 clauses / SAT | 0.204585 | **0.209642 (worse)** |
| 46 clauses / UNSAT | 0.062894 | **0.064484 (worse)** |

## Economic cost and meaning

- **Median feature extraction**: 0.158665 ms. **Median DPLL**: 0.268364 ms, measured in the same GitHub Actions run. Even without false positives, unconditional feature work is a large fraction of the reference solver cost. These are single-run Python timings on tiny formulas; do not extrapolate to Kissat or large instances.
- The independent n=10 test **limits** rather than confirms the structural-hardness interpretation of W037/W038. Predictive effects beyond clause count remain real for those specific samples, but this deliberately controlled test finds little independent information about search cost *within* satisfiability classes.
- This does not imply all geometric, physical or Fourier descriptors are useless, nor that the observed effect on SAT status is itself negligible. It does falsify any simple claim that the *current three features* already robustly measure complexity independently of size and satisfiability.

## W040 next decision

Prioritize a **published-source, family-held-out** evaluation with source-verifiable hashes and either matched SAT/UNSAT labels or unsatisfiable-only/satisfiable-only families. Compare cheap geometry against strong known SAT features and direct branching proxies, and charge feature extraction into end-to-end solver runtime. Consider more informative interaction features (constraint frustration, local propagation sensitivity, conditional entropy) only as prospective hypotheses, not after-the-fact tuning on W039's labels. Do not claim a theorem or speedup without independent evidence.
