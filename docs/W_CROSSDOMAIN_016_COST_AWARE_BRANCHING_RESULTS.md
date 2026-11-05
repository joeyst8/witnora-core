# W-CROSSDOMAIN-016 — Prospective cost-aware wave branching results

**Result: full correctness verification PASSED; the tested wave-guided DPLL strategy is slower end-to-end than a cheap degree heuristic on all three new formula families.** The negative result is retained without tuning the frozen gate or selecting examples by outcome.

## Precommit, implementation and CI provenance

- Prospective frozen protocol: `docs/W_CROSSDOMAIN_016_COST_AWARE_BRANCHING_PROTOCOL.md`, committed at `89f47d1c2b6279daf394c5f9b396c81417b8e9b9` **before examining W-016 solver outcomes**. A 12-decimal floating-point tie-handling clarification was made in the code commit before results.
- Native Rust implementation, CLI, independent Python truth-table/branching oracle, and focused GitHub Actions gate: commit `f1955d702ec438b7182eb336febe00adec2a91d2`.
- **Focused Rust migration workflow SUCCESS**: <https://github.com/joeyst8/witnora-core/actions/runs/42096627027>, including W-016 independent controls and the wider R-067–R-500 gates.
- **Full native Rust workflow SUCCESS**: <https://github.com/joeyst8/witnora-core/actions/runs/42096626767>.
- Test populations: three new, fixed-seed, 12-variable 3-CNF families of 32 instances each, not recycled from W-014/W-015. The selected Walsh row was determined by a frozen, unsigned structural overlap rule, not by outcomes. The gate used the precommitted `0.02`-bit mutual-information threshold.

## New prospective solver outcomes

All four policies were identical complete DPLL search procedures with fixed false-then-true branch polarity and exact 12-variable truth-table SAT verification. They differed only in static variable ordering:

| Family | SAT / UNSAT cases | Ascending mean scans | Degree mean scans | Wave mean scans | Fixed 0.02-bit gate mean scans | Cases gate chose wave |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Planted SAT (48 clauses) | 32 / 0 | 536.375 | **503.625** | 520.3125 | 522.6875 | 29 / 32 |
| Uniform boundary (48 clauses) | 23 / 9 | 966.5625 | **701.0625** | 855.53125 | 841.375 | 29 / 32 |
| Embedded easy UNSAT (56 clauses) | 0 / 32 | 198.000 | 254.4375 | **229.46875** | **229.46875** | 32 / 32 |

Wave branching increased DPLL scans by **3.31%** on planted SAT and **22.03%** on uniform boundary versus degree. On the deliberately easy embedded UNSAT control, it reduced DPLL clause scans by **9.81%** versus degree, although the fixed ascending order did even better. The gate's threshold was insufficiently selective: it chose wave on 90 of 96 formulas. This is a real unfavorable result, not a failure of exactness.

## End-to-end time: the decisive comparison

The native CLI measured the **full feature-selection + Fourier moment extraction + entropy/order calculation + DPLL** pipeline for wave and gated wave, and degree calculation + DPLL for the degree baseline. Same GitHub CI host, 20 alternating execution-order repetitions per case. These totals cover `32 * 20 = 640` executions per family and policy. Times are descriptive **host-dependent** observations; there is no claim of statistically stable hardware-independent ratios.

| Family | Degree pipeline total | Wave pipeline total | Fixed gate pipeline total | Wave slowdown relative to degree |
| --- | ---: | ---: | ---: | ---: |
| Planted SAT | 2.758 ms | 4.911 ms | 5.195 ms | **+78.1%** |
| Uniform boundary | 4.772 ms | 7.079 ms | 7.364 ms | **+48.4%** |
| Embedded easy UNSAT | 1.111 ms | 3.567 ms | 3.604 ms | **+221.0%** |

The wave policy is slower in **all three** families when measuring real work, including the control where it saves some DPLL clause scans. There is **no observed end-to-end benefit** from the current exact-frequency extraction, sorting, or simple gate.

## Where the overhead comes from

The source-scope selection itself costs more than the actual low-support Walsh expansion in counted operations. Mean per formula:

| Work counter | Planted SAT | Uniform boundary | Embedded UNSAT |
| --- | ---: | ---: | ---: |
| Unsigned clause-overlap comparisons in four-row selection | 274 | 274 | 322 |
| Selected-clause visits in exact 16-term Fourier expansion | 26.84 | 26.91 | 26.00 |
| Selected-literal visits | 69.50 | 70.06 | 59.00 |
| Variable-moment updates | 19.47 | 21.06 | 12.00 |

These are not interchangeable CPU operation units. Their practical significance is confirmed by the observed pipeline time rather than inferred from raw counts. The selected four-clause row is not free, and a finite-information feature is not useful if extracting it costs more than the search work it prevents.

## Scientific interpretation and future route

1. The W-014 predictor's useful mutual information does **not** automatically yield a good branching strategy. Specifically, entropy reduction about the selected violation *parity* is not entropy reduction about **future DPLL conflicts and propagation**.
2. The 0.02-bit gate is a weak operating rule. It was frozen before outcomes and **must not be retroactively optimized** on these 96 instances to report a fresh positive result.
3. A promising different hypothesis is a **much cheaper first-stage conflict/propagation estimator**, used to decide *whether* deeper spectral analysis would have positive expected computational value, followed by direct lookahead only on uncertain cases. Compare this prospectively on new graph distributions, with overall wall time and timeouts as the primary outcomes.
4. For efficiency, investigate calculating or maintaining several informative local moments **incrementally as DPLL assigns variables**, rather than rescanning all candidates to select a four-clause row at every root. This is a research proposal, not an established speedup.
5. Continue checking primary work in information-theoretic search, statistical-physics SAT propagation, and empirical algorithm selection. See the prior-literature links in `W_CROSSDOMAIN_015_STATISTICAL_WAVE_BRANCHING.md`.

This experiment has **no implication for a worst-case SAT improvement or for `P = NP`**. The useful new conclusion is that the **overhead and actionability bottlenecks are real and measured**, which should guide the next experimental design.
