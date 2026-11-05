# W-GEOMETRY-002 — Exact ground-state barrier curves by component factorization

**Status:** Rust implementation and independent tests written; Python analytical checks passed; native Rust compilation/differential CI pending. This is an integration of established statistical-physics energy landscapes, 0-dimensional filtered graph connectivity and Cartesian-product decomposition, **not** a novel general SAT solver.

## Physics + topology + algorithms: precise question

For a source CNF \(F\), let \(E_F(x)\) be the number of violated **original source clauses** at Boolean assignment \(x\). The Boolean hypercube has an edge for each single-variable flip. Let \(S=\{x:E_F(x)=0\}\) be the satisfying assignments (*ground states*).

For integer energy budget \(t\ge0\), two ground states \(x,y\in S\) are equivalent, denoted \(x\sim_t y\), if there is a Hamming-one path from \(x\) to \(y\) on which **every intermediate assignment** has \(E_F\le t\). Define:

- \(C_F(t)\): number of equivalence classes of *satisfying assignments* under \(\sim_t\).
- \(L_F(t)\): largest number of satisfying assignments in a class.
- \(B_F\): the smallest energy threshold for which \(C_F(t)=1\), if any satisfying assignment exists; otherwise `None`.

These curves quantify the temporary energy needed to move between solutions. **They are not the Betti-0 counts of all sublevel-set components**: a component containing only non-satisfying assignments is intentionally excluded. This distinction prevents an incorrect claim about full persistent homology.

## Exact factorization theorem (elementary, prior-art ingredients)

Suppose the source CNF separates into variable-disjoint primal components \(F_1,\ldots,F_k\). Then \(S=\prod_i S_i\) and energies add, \(E_F(x)=\sum_iE_{F_i}(x_i)\). For ground states \(x,y\),

\[
x\sim_t y\quad\Longleftrightarrow\quad
\text{for every component }i,\ x_i\sim_t y_i.
\]

**Forward direction:** project a global path of energy at most \(t\) onto each component. Local energies are nonnegative, so each projected path has local energy at most \(t\). **Backward direction:** take paths within each component sequentially, holding all other components at zero-energy assignments. Their total energy never exceeds \(t\). Every step flips one original variable.

Consequently,

\[
C_F(t)=\prod_i C_{F_i}(t),\qquad
L_F(t)=\prod_i L_{F_i}(t),\qquad
B_F=\max_i B_{F_i}
\]

when the source is satisfiable. These formulas concern only the *equivalence relation restricted to ground states*. The analogous product formula for all components of the full energy sublevel graph is **not** asserted.

## Rust implementation

- `rust/witnora-ve/src/aux_ground_barriers.rs`: validates signed source literals and component width, enumerates assignments only within each capped primal component, groups local states by number of violated source clauses, and incrementally activates states as \(t\) rises.
- A union-find data structure merges Hamming-one neighbors once both are active. At each threshold it counts only connected classes containing **ground states**, and the number of ground states in the largest such class.
- Exact global counts and largest sizes are the checked-`u64` products of local values at the same threshold. Output length is \(m+1\), for thresholds \(0\) through the total original source clause count \(m\).
- `aux_ground_barriers_native` exposes `(models, ground_cluster_counts, largest_ground_cluster_sizes, barrier)` through the Rust Python wheel.
- `tests/test_ground_barriers_rust.py` compares all thresholds against an **independent source-literal Python truth table + full sublevel graph BFS**, including 150 randomized CNFs, unsatisfiable sources, free variables, and strict caps.

**Hard limits:** at most 32 total variables, 64 source clauses, and 14 variables in each original source-primal component. Larger connected sources fail closed. The per-component truth table remains exponential; this does **not** bypass general SAT/#SAT hardness. An empty source clause forces zero ground states; an empty *formula* permits all assignments.

## Analytical 24-variable control: 4,096 islands merge at energy one

For each of twelve independent variable pairs \((x_i,y_i)\), impose the equivalence \(x_i=y_i\) using two source clauses

\[
(x_i\lor\neg y_i)\land(\neg x_i\lor y_i).
\]

Each pair has two satisfying assignments, `00` and `11`, which are **not adjacent** by one bit flip. Either intermediate state `01` or `10` violates exactly one clause, so its two ground states connect at energy budget one. For twelve independent pairs:

| Geometric quantity | Energy budget 0 | Energy budget 1 |
|---|---:|---:|
| Satisfying assignments | 4,096 | 4,096 |
| Ground-state connectivity classes | **4,096** | **1** |
| Largest ground-state class | **1** | **4,096** |

Thus \(B_F=1\). The formula has **24 variables and 24 clauses**, but each component needs only four local assignment evaluations. This does **not** mean every state at energy one is globally connected for unrelated formula families; it is an exact statement about this specified source.

## Matched-topology W-CROSSDOMAIN-009 controls

The earlier six-variable witness formulas each have two satisfying assignments, the same graph, the same #SAT, and the same full violation-energy histogram.

- Formula A: \(C(0)=2\), \(C(1)=1\), \(B=1\).
- Formula B: \(C(0)=1\), \(C(1)=1\), \(B=0\).

Their *barrier curves* distinguish the two sources even though ordinary violation counts do not. This is a finite structural observation, **not** yet evidence that higher barriers imply longer solver runtime.

## Verification and negative controls

1. Python analytical tests passed locally for the 24-variable family and both six-variable witnesses; a fully enumerated four-variable/two-component version independently confirmed the barrier transition.
2. Native Rust unit tests and 150 seeded direct-vs-native differential tests are wired to CI. With no Rust toolchain in the local workspace and no CI result reported at writing time, **Rust compilation and native correctness remain unverified**.
3. Contradictory unit clauses and explicit empty clauses must produce `models=0`, zero cluster counts, and no barrier. The empty formula with 32 free variables must produce \(2^{32}\) models and one zero-threshold class without enumerating \(2^{32}\) states.
4. **Do not** treat \(B_F\) as a proven complexity/hardness measure. Next validate whether it adds predictive value beyond \(n,m\), treewidth/separators, #SAT, ordinary spectra, and Witnora's Fourier signatures on held-out benchmarks with measured native solver steps.
5. Connected large sources remain unsolved by this factorization. Combining branches across separators requires exact boundary adjacency tracking; merely multiplying branch cluster counts would be wrong.

## Primary research context

- **“Barriers and Local Minima in Energy Landscapes of Stochastic Local Search”**: SAT as an energy landscape on the Boolean cube; <https://arxiv.org/abs/cs/0611103>.
- **“A Roadmap for the Computation of Persistent Homology”**: topological filtrations and component persistence; <https://doi.org/10.1140/epjds/s13688-017-0109-5>.
- Rina Dechter, **“Bucket Elimination: A Unifying Framework for Reasoning”**: exact factorization and conditioning as prior-art algorithmic context; <https://www.sciencedirect.com/science/article/pii/S0004370299000594>.

**Claim boundary:** an exact structural fingerprint for a bounded component-factorizable class; no new general complexity theorem or solver speedup has been established.
