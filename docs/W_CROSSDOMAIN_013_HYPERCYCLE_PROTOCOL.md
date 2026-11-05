# W-CROSSDOMAIN-013 — Prospective GF(2) even-incidence hypercycle selection

**Protocol frozen before examining the new family results.** W-CROSSDOMAIN-012 showed that fixed clause-position parity worsened prediction in its regular cyclic 3-CNF hypergraph, despite helping in an irregular one. This experiment asks whether an *algebraically selected* parity row is more robust on **fresh signed 3-CNF incidence hypergraphs**. Neither a positive nor a negative outcome is a complexity-class result.

## Frozen hypergraphs

Use six variables, six indexed clauses of width three, and independent signs at each of the 18 literal occurrences. Every graph contains all six variables, so `2^18 = 262,144` signings split into exactly `4,096` variable-flip gauge orbits. No results from these graph families were examined before freezing this protocol.

- **P1 — Pasch core with offset attachments:** `(1,2,3),(1,4,5),(2,4,6),(3,5,6),(1,2,4),(3,4,5)`; decreasing variable-incidence degrees `(4,3,3,3,3,2)`.
- **P2 — Pasch core with shared-vertex attachments:** `(1,2,3),(1,4,5),(2,4,6),(3,5,6),(1,2,4),(1,2,5)`; degrees `(4,4,3,3,2,2)`.

The first four triples in each family form a **binary even-incidence clause subset**: every variable participates in exactly two of those four clauses. These two new hypergraphs are non-isomorphic by degree sequence. Structural-only permutation checks also ruled out variable-renaming isomorphism with the T1/T2 pilot hypergraphs, including the T2/P1 pair with identical degree sequence. The signed search costs were not consulted for family selection.

## Fixed topology-to-parity rule

Construct the unsigned source incidence matrix `H` over `GF(2)` with one row per source clause and one column per variable. Examine all nonempty source-clause subsets `s` satisfying `s^T H = 0 (mod 2)`; select the subset with **minimum Hamming weight**, breaking ties by the numerically smallest little-endian clause-index bitmask. This bounded `m=6` implementation scans at most 63 subsets. On both frozen families the selected row is `[0,1,2,3]`, a size-four even-incidence hypercycle. This is established binary linear algebra, not a newly discovered theorem.

**Computational warning:** this exhaustive *minimum-weight* null-vector selection is not claimed efficient in general; a scalable implementation would need a different, explicitly budgeted GF(2) basis rule, and minimum-support problems can be difficult. Also, parity of the clause-violation vector should not be conflated with a Boolean XOR constraint on the variables.

## Locked test and predeclared failure threshold

- Run all `4,096` canonical polarity representatives per family, using direct 64-assignment truth tables and an independent Rust Fourier syndrome projector on the selected parity row. All-clause parity remains the zero-information negative control.
- Reuse the **unchanged** six-variable fixed-order DPLL full-model counter and its clause-scan instrumentation from W-CROSSDOMAIN-012. Compare exact source model counts for both ascending and descending variable order.
- Within each family, compare LOO MSE using the full energy histogram `A` versus grouping additionally by the parity-conditioned histogram `E`. Exclude singleton `A` groups and fall back to `A` for singleton `(A,E)` groups.
- Run 1,000 seeded within-energy permutations. The frozen *strict replication criterion* is positive LOO-MSE improvement and exploratory add-one p at most `0.0125` in **all four family/order combinations**. Mark NOT MET if any fail, without changing graphs or parity rule afterward.
- For each family/order, report the fraction of instances where exact feature enumeration's 384 clause scans exceed the DPLL clause scans. The additional bounded hypercycle selection and Fourier validation are not included in that 384-scan count; no wall-clock inference is allowed.

## Mandatory limits and independent verification

All six-clause width-three formulas are SAT by the 64-minus-48 union bound (at least 16 models), so this remains a *model-counting search-tree variation* test rather than UNSAT hardness. Family-conditional LOO is not an out-of-graph-trained predictor. Feature extraction already visits every assignment; a positive predictive result alone would not justify running it as a solver heuristic.

Implement a Rust `witnora_hypercycle` JSON CLI and independent Python controls checking incidence-nullspace selection, raw signed source, exact histograms, DPLL counts/scans and the four-way criterion. Verify full GitHub Rust CI before recording any outcome; preserve negative results and raw metrics.

## Prior mathematics

- G. D. Forney Jr., *Codes on Graphs: Duality and MacWilliams Identities*, IEEE Transactions on Information Theory (2011), <https://arxiv.org/abs/0911.5508>.
- A. Al-Bashabsheh and Y. Mao, *On Factor Graphs and the Fourier Transform*, IEEE Transactions on Information Theory (2005), <https://ieeexplore.ieee.org/document/1424306/>.
