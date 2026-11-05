# W-GEOMETRY-001 — Exact Hamming geometry from source-CNF components

**Status:** Rust implementation and independent controls prepared, Python analytical checks pass; native compilation and Rust differential tests await CI. **Established mathematical construction** (Cartesian products and Walsh autocorrelation), not a new general SAT/#SAT algorithm or solution of P vs NP.

## Geometric idea

Represent each complete Boolean assignment as a vertex of the \(n\)-dimensional Hamming cube. Two assignments are adjacent when one variable changes. For source CNF \(F\), keep only the vertices satisfying **every original source clause**. The induced subgraph \(G_F\) encodes whether solutions are connected under single-variable flips.

The exact output is:

- \(N=\lvert S_F\rvert\): model count.
- \(c(G_F)\): number of connected solution clusters.
- \(L(G_F)\): largest cluster size.
- \(D_F(t)=\#\{(x,y)\in S_F^2:\ d_H(x,y)=t\}\), with **ordered pairs**, including \(x=y\) at distance zero.

These have strict checks \(D_F(0)=N\) and \(\sum_tD_F(t)=N^2\). A cluster measure is not a complete characterization of the graph; two different solution graphs may share these summaries.

## The two exact shortcuts

**1. Cartesian-product factorization.** For source formulas on variable-disjoint primal components \(F=F_1\wedge\dots\wedge F_k\), the solutions are a product \(S_F=\prod_i S_{F_i}\), and the solution-induced Hamming graph is the Cartesian product of local graphs. Consequently,

\[
N=\prod_i N_i,\quad c(G_F)=\prod_i c(G_{F_i}),\quad
L(G_F)=\prod_iL(G_{F_i}),\quad D_F(z)=\prod_iD_{F_i}(z).
\]

Here the polynomial \(D(z)=\sum_tD(t)z^t\) multiplies because Hamming distances **add across variable-disjoint components**. A formula containing an empty source clause has \(N=c=L=0\) and the zero distance polynomial.

**2. Walsh autocorrelation inside each component.** Let \(f(x)\in\{0,1\}\) indicate whether local assignment \(x\in\mathbb F_2^k\) satisfies all local clauses. For each bit-flip mask \(z\), the number of ordered satisfying pairs with XOR difference \(z\) is

\[
A(z)=\sum_x f(x)f(x\oplus z).
\]

Under the unnormalized Walsh–Hadamard transform, \(\widehat A(\omega)=\widehat f(\omega)^2\). The inverse Walsh transform divided by \(2^k\) recovers all exact integer \(A(z)\). Summing by \(\lvert z\rvert\) gives the local ordered Hamming-distance polynomial in \(O(k2^k)\) transform operations after computing the local truth table, rather than enumerating every satisfying pair in \(O(\lvert S\rvert^2)\).

The identities are established Fourier/coding-theory techniques, not Witnora-specific theorems. The benefit comes from combining them with *source-exact component detection* and explicit fail-closed limits.

## Rust implementation and bounds

- `rust/witnora-ve/src/aux_solution_geometry.rs`: `exact_solution_geometry(source, nvars, max_component_variables)`; validates signed source literals, decomposes the primal graph, exhaustively evaluates each capped component, computes local Hamming-one connectivity and Walsh autocorrelation, and combines the exact summaries with checked integer arithmetic.
- `rust/witnora-ve/src/lib.rs`: `aux_solution_geometry_native` exposes `(models, clusters, largest_cluster, distance_coefficients_as_decimal_strings)` through the Python wheel. Decimal strings preserve the full 128-bit pair counts.
- `tests/test_solution_geometry_rust.py`: an **independent literal-level Python truth table and graph BFS** for 150 random small source CNFs, plus analytic large-component-product checks.
- `rust-migration-fast.yml`: Rust library tests and an explicit Python native import/differential gate.

**Caps:** at most 32 total variables, 64 clauses, and 14 variables per original primal connected component. Large connected source formulas fail closed; this is **not** a general polynomial-time method for deriving solution geometry. Local truth-table cost still scales exponentially in component width. Checked `u128` convolution handles ordered pair totals exceeding `u64`.

## Controls and exact numerical expectations

### 24-variable, 12-component analytic family

For twelve independent positive binary clauses \((x_{2j-1}\lor x_{2j})\), each two-variable component has three satisfying assignments, one connected cluster, and ordered pair-distance polynomial \(3+4z+2z^2\). Thus

\[
N=3^{12}=531441,\quad c=1,\quad L=531441,\quad
D(z)=(3+4z+2z^2)^{12}.
\]

The ordered satisfying-pair total is \(D(1)=N^2=282429536481\); the Rust algorithm need not enumerate these more than 282 billion pairs. Python analytical assertions passed; native Rust remains pending.

### 32 completely free variables

All \(2^{32}=4294967296\) assignments satisfy an empty **formula** (which must not be confused with an empty *clause*). Its solution cube is connected, and

\[
D(t)=2^{32}\binom{32}{t},\qquad\sum_tD(t)=2^{64}.
\]

The result contains 33 exact integer coefficients, representing more than 18 quintillion ordered satisfying pairs without enumerating any pair.

### Matched six-variable formulas from W-CROSSDOMAIN-009

Both formulas have two satisfying assignments, the same source primal graph, and identical energy histograms \((2,22,30,10,0,0,0,0)\). Yet the first has two **isolated** solutions (Hamming distance six), while the second has one two-vertex connected component (Hamming distance one):

| Geometry measure | Formula A | Formula B |
|---|---:|---:|
| Models | 2 | 2 |
| Solution clusters | 2 | 1 |
| Largest solution cluster | 1 | 2 |
| Ordered distance polynomial | \(2+2z^6\) | \(2+2z\) |

This demonstrates that **solution geometry** contains information absent from #SAT and the unconditioned violation-energy histogram for this finite source pair. No inference about generic solver hardness is justified from this witness alone.

## Required next checks and limitations

1. Compile and run the Rust-native gates; no local Rust toolchain was available at implementation time, and GitHub CI results have not yet been observed.
2. Validate on held-out, non-isomorphic graphs while matching size, treewidth/separator descriptors, model count and energy histogram. Correlation with **actual measured solver work** is the relevant next hypothesis.
3. For connected large sources, investigate *separator-conditioned boundary connectivity*: naïvely multiplying component cluster counts after conditioning on a separator is generally **incorrect** because different separator assignments can be adjacent by flipping a separator variable.
4. Preserve gauge/variable-complement equivalence from W-CROSSDOMAIN-009. The construction respects Hamming isometries; an additional permutation-invariance control should be tested.

## Prior literature (primary)

- G. David Forney Jr., **“Codes on Graphs: Duality and MacWilliams Identities,”** *IEEE Transactions on Information Theory* (2011): <https://arxiv.org/abs/0911.5508>.
- Cartesian graph-product connectivity results, including the product connectedness criterion, appear in graph-product research: <https://www.sciencedirect.com/science/article/pii/S0893965907002236>.
- **“Barriers and Local Minima in Energy Landscapes of Stochastic Local Search,”** research on SAT landscapes in the Boolean hypercube: <https://arxiv.org/abs/cs/0611103>.

**Research boundary:** exact small-component geometry with implicit large products is a useful verified direction, but not itself evidence of a new complexity class or polynomial-time SAT solution.
