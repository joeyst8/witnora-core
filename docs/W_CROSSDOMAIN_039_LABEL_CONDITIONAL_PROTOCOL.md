# W039 — Frozen label-conditional geometry test (independent n=10 generation)

**Prospective protocol. Commit this design and code to GitHub before inspecting the W039 evaluation output.** W038's post-hoc SAT-label control reduced the associated improvement to 2.75%; W039 independently tests whether a three-feature structural signal survives conditioning on SAT versus UNSAT status as well as clause count.

## Sample construction (freeze before run)

- A **new** random 3-CNF family with exactly **10 variables** and **180 accepted source formulas**.
- Clause counts exactly `(38, 42, 46)`. At each clause count, accept exactly 30 SAT and 30 UNSAT instances (six cells, 30 each).
- Generate the 960 distinct non-tautological 3-literal clauses from `choose(10,3)` variable triples and all eight polarity patterns. For each `m` in ascending order, repeatedly `random.Random(390039).sample(pool,m)` without replacement *within the formula*, retaining generated clause order, until both SAT and UNSAT cells have 30 samples. Attempt limit 20,000 per clause-count group, otherwise stop with an explicit failure. No case selection based on solver search cost.
- Determine SAT/UNSAT for *sampling* using a separate exact 1,024-assignment Boolean truth-mask enumerator, **not the DPLL whose scan count is our target**. Verify the retained labels afterward against DPLL. Recompute all samples exactly in integrity replay.
- Do not use the truth label in any geometry feature, but include it in the **research-only matching baseline**. This conditional test is not itself a deployable feature router because the SAT label would generally be unknown during solving.

## Precommitted features, predictions and inference

- Use **only** the W038 preselected cheap three source features, unmodified: signed literal-degree imbalance, exact incidence-derived clause overlap, and absolute spectral radius of the signed variable co-occurrence matrix. No feature selection or feature modification after observing outcomes.
- Dependent variable: `log1p(exact DPLL source-clause scans)` using the frozen transparent W035 reference implementation, same clause order.
- Holdout: fixed fivefold stratified by **(clause count, SAT label)**. Seed `390040`, shuffle cell rows and assign `position % 5` (six held-out cases per cell per fold).
- Primary baseline: **six one-hot indicators of the full (clause count, SAT status) cells**, not separate main effects. Enhanced model adds the three within-training-fold standardized geometry features; ridge penalty **10** on the three feature slopes, zero penalty on the six cell intercepts.
- Primary statistic: relative out-of-fold mean squared-error reduction, `(MSE_base - MSE_geometry) / MSE_base`. Also report MAE, each of the six cells' errors, and wall-clock feature extraction compared to DPLL in the same CI process.
- Null test: **499** feature-vector permutations **within each (m, SAT/UNSAT) cell**, seed `390041`, fixed folds and retraining each time. One-sided p-value `(1 + #permutations >= observed) / 500`. Report even if negative; permutation granularity floor 0.002. The null is conditional exchangeability in this synthetic sampling design, not a general physical law.
- Secondary: size-only baseline versus size plus the same three features on these same samples. This is descriptive and cannot be a replacement for the label-conditional primary test.

## Integrity, limitations, and advance criteria

The repository must archive all accepted original clauses, generated attempt indices, oracle labels, DPLL scans, features, within-cell folds, held-out predictions, null values and extraction timings. An independent CI workflow must reconstruct samples, verify bitmask ground truth and DPLL, and replay the statistics from the archived raw artifact and hashes.

Positive conditional prediction across this independent n=10 family would justify a family-held-out **published-source** replication, not imply an efficient SAT solver. Prior W037/W038 tests guided the feature choice, so do not combine their p-values as if all choices were preplanned. A negative or mixed result is scientifically informative and must remain in the record.
