# W-CROSSDOMAIN-011 — Prospective non-isomorphic graph replication protocol

**Protocol frozen before inspecting either held-out graph's search-cost results.** This experiment tests the finite W-CROSSDOMAIN-010 cycle-spectrum/branch-cost association for two structurally different signed 2-CNF graphs. It does not claim a result on general SAT, 3-SAT, complexity classes, or efficient feature extraction.

## Exact graph selection, fixed before running the audit

Reuse the W-CROSSDOMAIN-010 original family as the calibration reference only:

1. **Original:** `(1,2),(1,3),(1,4),(2,3),(2,5),(4,6),(5,6)`; sorted vertex-degree sequence `(3,3,2,2,2,2)`.
2. **Holdout H1 — double-triangle tail:** `(1,2),(1,3),(1,4),(2,3),(2,4),(3,5),(5,6)`; degrees `(3,3,3,2,2,1)`.
3. **Holdout H2 — two leaves and a shared triangle:** `(1,2),(1,3),(1,4),(2,3),(2,5),(2,6),(3,4)`; degrees `(4,3,3,2,1,1)`.

These degree multisets prove the three indexed graphs are pairwise non-isomorphic. Every graph is connected, has six active vertices and seven indexed edges, and contains the *same predeclared clause-index triangle* `[0,1,3]` on vertices `(1,2,3)`. Different cycle structures are accepted rather than matched away. No graph was selected for its observed results.

## Locked algorithm and outcome before examining holdout results

- Enumerate all `2^14 = 16,384` signed endpoint assignments per graph; quotient the six independent Boolean variable-flip/gauge orbits to 256 canonical representatives per graph. Explicitly verify that no variable is isolated and canonicalization maps to 256 representatives.
- For each representative enumerate all 64 Boolean assignments to get the exact violation-weight histogram `A` and triangle-even histogram `E`. Independently check `E` using the existing Rust Walsh/Fourier projection.
- Use the **unchanged** deterministic DPLL full-model counter from W-CROSSDOMAIN-010, with unit propagation and recursive-call count. Run ascending and descending fixed variable orders; both model counts must equal `A[0]`. Do **not** optimize variable order for these families.
- Within each graph, compare leave-one-out mean squared error for grouping by `A` alone versus `(A,E)`, excluding any energy group with only one representative from both estimators and falling back to the energy-only predictor for singleton `(A,E)` groups.
- Reuse 1,000 seeded, within-energy-group permutations for each graph and order. These tests are exploratory: conditional permutation frequency is *not* an independent out-of-sample generalization p-value and feature labels require exact enumeration.
- **Predeclared strict replication criterion:** both held-out graphs must show *positive LOO-MSE improvement for both orders*, and each of the four within-graph permutation add-one p-values must be at most `0.0125` (Bonferroni bound for four exploratory checks). If any fail, report failure of this strict criterion; do not silently change graphs, cycle rows, branch orders, thresholds or exclusion rules.

## Negative controls and possible failure modes

This is a **graph-heldout replication**, not a train-on-G1/test-on-G2 learned predictor: category-wise LOO means are recomputed *inside* each held-out graph and use other examples from that graph. Correlated orbit representatives and retrospective feature selection in W-CROSSDOMAIN-009 limit generalization. Even success across these two small **2-SAT** graphs would not address the intrinsic exponential-time difficulty of arbitrary SAT; a production feature must be computable more cheaply than its prospective benefit.

## Verified results — 2026-11-05

Both frozen holdout families passed the exact Rust audit and the independently implemented Python source-literal/DPLL controls. Source reconstruction, all four reference-mask truth tables and both DPLL-order model counts matched. All 256 gauge representatives in each family passed the native Fourier-parity cross-check.

| Frozen family / decision order | LOO samples | Energy-only MSE | Energy + triangle MSE | Error reduction | Conditional permutation tail |
|---|---:|---:|---:|---:|---:|
| H1 / ascending | 243 | 3.3391 | 2.7068 | **18.94%** | 0 / 1,000 |
| H1 / descending | 243 | 3.5802 | 2.6157 | **26.94%** | 0 / 1,000 |
| H2 / ascending | 246 | 1.3761 | 1.3212 | **3.99%** | 1 / 1,000 |
| H2 / descending | 246 | 1.1340 | 0.7886 | **30.46%** | 0 / 1,000 |

The original graph had 80 distinct energy profiles and 135 energy-plus-triangle spectra. H1 had **82** and **122**, respectively; H2 had **70** and **104**. These are exact finite-family counts, not entropy rates.

**Strict predeclared four-way criterion: MET.** All four improvements are positive and their add-one conditional permutation p-values are respectively `0.000999`, `0.000999`, `0.001998`, and `0.000999`, below the specified `0.0125` Bonferroni threshold. This criterion was frozen in commit `96a80bd4a21e468b99e31d0b85d2764f6bf48510` before the implementation/results commit `79d40fe8b7791b663f2bf06b8dd4b2705d6d23fa`.

**Independent CI provenance:**

- Rust native differential gate: [all 84 steps passed](https://github.com/joeyst8/witnora-core/actions/runs/42084011305).
- Focused Rust research gate, including the new W-CROSSDOMAIN-011 CLI and two independent Python oracle tests: [all 28 steps passed](https://github.com/joeyst8/witnora-core/actions/runs/42084011271).

**Scientific qualification:** this is prospective *graph selection* but a within-graph, exact-enumeration predictor. It is not a learned out-of-graph prediction, statistical independence, a scalable feature, a solver speedup, or a P versus NP result. The near-zero H2/ascending improvement is an important warning against treating the original ~42–53% gains as universal. The next experiment must include mixed-width 3-CNF and computational-cost accounting for the predictor itself, with its test protocol frozen before observing outcomes.

## Implementation targets

- Parameterize the Rust W-CROSSDOMAIN-010 audit by graph edge list without changing the original witness regression.
- Add `witnora_cycle_holdout` Rust JSON CLI and independently reconstructed Python truth-table/DPLL checks for fixed masks on both new graphs.
- Gate the new study in the focused Rust GitHub workflow; record complete results *including negative outcomes* and native CI links in this file after verification.

## Established related ideas

- G. D. Forney Jr., *Codes on Graphs: Duality and MacWilliams Identities*, IEEE Transactions on Information Theory (2011), <https://arxiv.org/abs/0911.5508>.
- Jinbo Huang and Adnan Darwiche, *A Structure-Based Variable Ordering Heuristic for SAT*, IJCAI (2003), <https://ijcai.org/proceedings/2003/166>.
- Bengt Aspvall, Michael F. Plass, and Robert Endre Tarjan, *A linear-time algorithm for testing the truth of certain quantified Boolean formulas*, Information Processing Letters (1979), <https://www.sciencedirect.com/science/article/abs/pii/0020019079900024> (the established polynomial-time 2-SAT boundary).
