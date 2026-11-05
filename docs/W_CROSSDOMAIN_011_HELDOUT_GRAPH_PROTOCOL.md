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

## Implementation targets

- Parameterize the Rust W-CROSSDOMAIN-010 audit by graph edge list without changing the original witness regression.
- Add `witnora_cycle_holdout` Rust JSON CLI and independently reconstructed Python truth-table/DPLL checks for fixed masks on both new graphs.
- Gate the new study in the focused Rust GitHub workflow; record complete results *including negative outcomes* and native CI links in this file after verification.

## Established related ideas

- G. D. Forney Jr., *Codes on Graphs: Duality and MacWilliams Identities*, IEEE Transactions on Information Theory (2011), <https://arxiv.org/abs/0911.5508>.
- Jinbo Huang and Adnan Darwiche, *A Structure-Based Variable Ordering Heuristic for SAT*, IJCAI (2003), <https://ijcai.org/proceedings/2003/166>.
