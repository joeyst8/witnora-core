# W-CROSSDOMAIN-014 — Wave-proxy result and limits

**Result: exact bounded Walsh character verified; feature extraction becomes much cheaper by counted clause visits; predictive benefit is mixed (3/4 positive), with no demonstrated solver speedup.**

## Provenance and scope

- Frozen exploratory protocol: `docs/W_CROSSDOMAIN_014_WAVE_PROXY_PROTOCOL.md`, preregistered in commit `e8c8f3fc65daaf8cb2e13f91de807d96d1c07e7d` before W-014 results.
- Rust implementation: `rust/witnora-ve/src/aux_wave_parity.rs`, `rust/witnora-ve/src/aux_three_cnf_geometry.rs`, and native `witnora_wave_proxy` CLI.
- Native code and independent Python controls: commits `9fedae3f693275a5a41ff2475adecd0d72f0ae2d` and `94b749ac65f2eab9dae24c358002e2945697c2e7`.
- GitHub Actions: focused run **42093146345 SUCCESS** (W-014 gate plus the wider regression), native run **42093146453 SUCCESS**, both on commit `94b749ac65f2eab9dae24c358002e2945697c2e7`.
- W-014 uses the previously inspected W-013 P1/P2 source families. These results are **exploratory**, not held-out confirmation or an independent mathematical discovery.
- Every formula in this six-variable, six-width-three-clause universe is **satisfiable** (at least 16 models), so this does not test hard UNSAT search.

## Exact frequency calculation

For the selected four-clause GF(2) incidence-kernel row `[0,1,2,3]`, compute the unnormalized Walsh coefficient

`B = sum_{x in {0,1}^6} (-1)^(sum_{c in C} v_c(x))`

by expanding `product_{c in C} (1 - 2 v_c(x))`. Each clause subset fixes a consistent partial assignment or contributes zero, so only **16 subset terms** are needed. The Rust coefficient matches direct assignment enumeration, the prior full energy/conditional parity spectra, and independent Python controls. Duplicate selected clause indices cancel modulo two; empty and conflicting clauses are included in Rust unit tests.

Observed per-source extraction work, identical across both families:

| Work counter | Value |
| --- | ---: |
| Walsh subset terms | 16 |
| Selected-clause visits, mean | 28.625 |
| Selected-clause visits, maximum | 32 |
| Literal visits, mean | 74.59375 |
| Literal visits, maximum | 96 |
| Prior exhaustive full-histogram clause checks | 384 |

These counts are **not equal-time CPU work units**: the Walsh method has bit-mask and subset-loop overhead; the pair-conflict baseline also performs up to 15 source-clause pair comparisons. Nevertheless, the bounded computation avoids the earlier 64-assignments-by-6-clauses sweep.

## Frozen prediction experiment

All 4,096 gauge-canonical source signings per family. Baseline: leave-one-out DPLL node prediction from a cheap 14-valued *pairwise violation-conflict count*. Enhanced feature: baseline count together with the single Walsh coefficient (five distinct coefficient values). Exclude singleton baseline groups as preregistered: 2 P1 rows and 1 P2 row. Fixed ascending and descending DPLL variable orders.

| Source family | DPLL order | Scored rows | Baseline LOO MSE | Wave LOO MSE | Error improvement | Exploratory shuffled-label p |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| P1 Pasch offset | Ascending | 4,094 | 11.680519 | 11.429887 | **+2.1457%** | 0.000999 |
| P1 Pasch offset | Descending | 4,094 | 14.927235 | 14.979278 | **-0.3486%** | 0.118881 |
| P2 Pasch shared vertices | Ascending | 4,095 | 9.433219 | 8.100321 | **+14.1298%** | 0.000999 |
| P2 Pasch shared vertices | Descending | 4,095 | 11.904887 | 11.408250 | **+4.1717%** | 0.000999 |

The 1,000 fixed-seed permutations shuffle wave labels *within the baseline pair-conflict strata*. Because P1/P2 have already been used for earlier W-013 research, the permutation diagnostics **must not be interpreted as prospective statistical evidence**. The P1 descending regression is a real negative result and was not suppressed.

Mean DPLL clause scans for reference: P1 ascending **353.23**, P1 descending **372.90**; P2 ascending **317.21**, P2 descending **434.59**. Wave selected-clause visits exceeded the measured DPLL clause scans on **0%** of formulas in all four settings, compared with the old exhaustive spectrum being costlier than DPLL on up to **97.71%** in W-013. These are again differently scaled operation counters, **not a CPU-time speedup**.

## Interpretation and next falsification target

1. We obtained an *exact* low-support spectral correlator at bounded feature cost, without enumerating all assignments.
2. The scalar correlator retains some search-cost prediction beyond source-level pair conflicts, **but not reliably in all variable orders**. It does not reconstruct the original energy-conditioned parity histogram.
3. The result is not a SAT decision algorithm, does not change worst-case DPLL complexity, and gives no implication for `P = NP`.
4. **W-015 candidate**: derive first-order *variable-conditioned* spectral responses from the same clause-subset expansion, use these to select a DPLL branching variable, and compare **end-to-end measured solver time, nodes and clause scans** against fixed-order and standard structural heuristics on preregistered, previously unseen mixed SAT/UNSAT instances. Budget feature extraction in the same operational units, record timeouts, and preserve negative outcomes.

Prior mathematical framework: Forney's codes-on-graphs Fourier duality and O'Donnell's *Analysis of Boolean Functions*, linked in the frozen W-014 protocol. The four-clause expansion itself is conventional Boolean Fourier/inclusion-exclusion algebra, not a new Fourier transform.
