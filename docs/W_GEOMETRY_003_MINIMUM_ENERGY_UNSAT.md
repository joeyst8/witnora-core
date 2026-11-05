# W-GEOMETRY-003 — Minimum-energy geometry of both SAT and UNSAT source CNFs

**Status:** Rust implementation and independent tests prepared; Python analytical checks passed; native Rust compilation and differential CI not yet verified. This is established Max-SAT/statistical-physics energy mathematics combined with exact Cartesian-product connectivity, **not** a general polynomial-time SAT/Max-SAT solver or evidence that P = NP.

## Why W-GEOMETRY-002 is incomplete

W-GEOMETRY-002 traces connectivity *among satisfying assignments* as a clause-violation energy allowance increases. For UNSAT formulas there are no zero-violation assignments, so that profile is identically empty and says nothing about the **lowest attainable energy**. Statistical physics instead calls *global energy minimizers* the ground states, even when their energy is positive. The corresponding computational-optimization problem is unweighted Max-SAT: minimizing the number of violated source clauses.

For CNF \(F\), write \(E_F(x)=\#\{\text{original source clauses violated by }x\}\), \(e_F=\min_x E_F(x)\) and \(M_F=\{x:E_F(x)=e_F\}\). The source is satisfiable **if and only if** \(e_F=0\). Define \(x\sim_t y\) for \(x,y\in M_F\) when a Hamming-one path from \(x\) to \(y\) remains inside the absolute energy threshold \(E_F\le e_F+t\). The experimental outputs are:

- Minimum number of violated clauses \(e_F\).
- Number of minimum-energy assignments \(\lvert M_F\rvert\).
- Counts and largest sizes of equivalence classes of minimizers for each *extra energy budget* \(t\).
- Smallest extra budget connecting all minimizers.

As in W-GEOMETRY-002, the counts cover **only components containing actual minimizers**, not every component of the full sublevel graph.

## Exact component theorem and proof

For source-primal variable-disjoint components \(F_1,\ldots,F_k\), plus \(e_\emptyset\) literal-empty clauses, the energy decomposes as

\[
E_F(x)=e_\emptyset+\sum_iE_{F_i}(x_i),\qquad
e_F=e_\emptyset+\sum_i e_{F_i}.
\]

Thus \(M_F=\prod_iM_{F_i}\), and the **excess energy** is an additive nonnegative sum:

\[
E_F(x)-e_F=\sum_i\bigl(E_{F_i}(x_i)-e_{F_i}\bigr).
\]

Any global path through states with excess energy at most \(t\) projects onto local paths with each local excess at most \(t\). Conversely, if all pairs of local minimizers can be joined under that local excess budget, join them **sequentially**, holding other components at their respective minima, so the global budget never exceeds \(t\). Therefore the minimizer-connectivity partition at threshold \(t\) is the Cartesian product of the local partitions; cluster counts and largest cluster sizes multiply, and the global connecting barrier is the maximum local barrier.

This is an elementary exact theorem for variable-disjoint source components. It does **not** extend unchanged to connected sources or arbitrary separator branches.

## Rust implementation

- `rust/witnora-ve/src/aux_min_energy_geometry.rs`: `exact_minimum_energy_geometry(source, nvars, max_component_variables)` validates source literals, finds independent primal components, exactly computes each local minimum-energy level, activates assignments in increasing **excess** energy, and merges Hamming-one neighbors using union-find.
- Component summaries are multiplied at matching excess budgets; literal-empty clauses shift the overall minimum energy without changing minimizer connectivity.
- `rust/witnora-ve/src/lib.rs`: Python-wheel binding `aux_minimum_energy_geometry_native` returns `(minimum_violations, minimizers, cluster_counts_by_extra_budget, largest_by_extra_budget, connection_barrier_extra)`.
- `tests/test_minimum_energy_geometry_rust.py`: an independent literal-level truth-table and sublevel-graph BFS oracle for 150 seeded small CNFs, plus analytical large-component families and strict failure controls. The focused native workflow imports the binding explicitly.

**Caps:** at most 32 total variables, 64 clauses, and 14 variables per original primal component. A connected component that exceeds the cap fails closed. The local step still enumerates \(2^k\) assignments for component width \(k\); no general-purpose complexity improvement is claimed.

## Main falsification control — an UNSAT 25-variable formula

Create twelve independent equality pairs \(x_i=y_i\) using two CNF clauses each, as in W-GEOMETRY-002, and introduce a twenty-fifth variable \(z\) with contradictory unit clauses \((z)\) and \((\neg z)\). The formula has 25 variables and 26 clauses and is **UNSAT**. However, exactly one of the two contradictory units is violated at any assignment, so its minimum energy is **one**.

Each equality pair has two zero-excess configurations, separated by a one-unit excess-energy barrier. The contradictory unit pair has two adjacent minimizers. The exact analytical result is:

| Quantity | Extra energy 0 | Extra energy 1 |
|---|---:|---:|
| Minimum violated clauses | 1 | 1 |
| Assignments attaining minimum energy | 8,192 | 8,192 |
| Separate minimum-energy clusters | **4,096** | **1** |
| Largest minimum-energy cluster | **2** | **8,192** |

The connecting barrier above the global minimum is one. The algorithm analyzes only twelve two-variable components and one single-variable component, not all \(2^{25}\) assignments. The analytical result was checked against a fully enumerated five-variable/two-pair instance, where four clusters merge into one at excess energy one.

## Negative controls and next scientific test

- For contradictory unit clauses \((x)\land(\neg x)\), minimum energy is one and both possible assignments are adjacent minimizers: cluster count one at extra energy zero.
- A source consisting solely of an empty clause has fixed energy one everywhere. All remaining free-variable assignments are minimizers, one connected cluster.
- For satisfiable formulas, \(e_F=0\) and the minimum-energy profile must agree **exactly** with W-GEOMETRY-002's zero-energy ground-state profile.
- **No P = NP implication:** obtaining the exact global minimum \(e_F\) for a general connected source is Max-SAT optimization, and the bounded source-component enumeration remains exponential in component width. The result applies only to structured families with small components.
- Next measure whether minimum-energy barrier curves provide additional information for hard **UNSAT** and near-threshold 3-SAT cases beyond \(n,m\), graph structure, solution count, and existing Fourier spectra. Use held-out graphs and *actual native solver work*; log negative or inconclusive results.

## Primary references

- **“Resolution for Max-SAT,”** *Artificial Intelligence* (2007): Max-SAT as minimizing violated CNF clauses; <https://www.sciencedirect.com/science/article/pii/S0004370207000422>.
- **“Complete Realization of Energy Landscapes and Non-Equilibrium Trapping Dynamics in Small Spin Glass and Optimization Problems,”** *Scientific Reports* (2024): <https://www.nature.com/articles/s41598-024-65493-4>.
- **“Barriers and Local Minima in Energy Landscapes of Stochastic Local Search”**: Boolean CSP energy landscapes; <https://arxiv.org/abs/cs/0611103>.

**Claim boundary:** a mathematically valid extension of bounded exact geometry measurements to UNSAT and near-solution regions; no novel general SAT complexity theorem has been obtained.
