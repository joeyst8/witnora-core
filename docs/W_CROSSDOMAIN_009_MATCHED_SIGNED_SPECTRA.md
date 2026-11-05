# W-CROSSDOMAIN-009 — Matched-topology falsification of sufficient violation spectra

**Status:** complete, deterministic finite Python enumeration; Rust source-level witness regression added; native Rust CI verified on 2026-11-05. **Finding: a predeclared cycle-parity spectrum separates some signed CNFs with identical topology, #SAT, and total-violation distributions.** No solver-runtime or mathematical novelty claim follows from this result.

## Research hypothesis and primary prior art

W-CROSSDOMAIN-005 established that undirected source graph features alone do not determine source-CNF #SAT. W-CROSSDOMAIN-008 supplied an exact Fourier projection onto clause-violation parity syndromes. This experiment asks a stronger and *falsifiable* question: can the **distribution of violations in a specific cycle of clauses**, conditioned on the *total* number of violated clauses, distinguish two formulas even if their ordinary energy histograms are identical?

The use of Fourier-weight/syndrome distributions and factor-graph duality is established (Forney, MacWilliams), as is studying frustration in signed networks. Our proposed structural *feature* is not claimed to be a newly discovered invariant or a source of algorithmic speedups. The important methodological point is matched control of graph, variable count, source clause count, model count, and energy histogram.

## Full finite universe

Fix six variables and the **same indexed** seven-edge primal graph in every case:

```
(1,2), (1,3), (1,4), (2,3), (2,5), (4,6), (5,6)
```

Each edge is a signed 2-clause; choose each endpoint literal's polarity independently, giving exactly \(4^7=16384\) signings. Enumerate all \(2^6=64\) source assignments for every signing. The parity row **was fixed before enumeration** to the three clauses forming triangle \((1,2),(1,3),(2,3)\): zero-based indices `[0,1,3]`.

For every signing, compute:

1. \(M\): number of zero-violation assignments (#SAT).
2. \(A_k\): number of assignments violating exactly \(k\) of the seven source clauses.
3. \(E_k\): among the same assignments, number with **even parity** of violations in the fixed triangle.

\(A_k-E_k\) is the odd-parity spectrum. This is an exact finite counting experiment, not a random sample.

## Result

| Discriminator | Distinct patterns across the 16,384 signings |
|---|---:|
| #SAT only \(M\) | **16** |
| Full violation-energy histogram \(A_0,\ldots,A_7\) | **80** |
| Energy histogram plus fixed triangle-even spectrum | **135** |

**30 of the 80 ordinary energy-histogram groups split into multiple distinct cycle-parity spectra.** This is strictly more descriptive information about the *signed constraints* than graph topology, #SAT, or the unconditioned energy histogram individually.

### Connection to discrete \(\mathbb Z_2\) gauge symmetry

If a variable is complemented in *every* assignment and every occurrence of its literal is simultaneously negated, each clause's truth value is unchanged under the assignment bijection. Thus **the entire violation vector distribution, including every parity spectrum, is gauge-invariant** under an independent flip of each variable. This is an elementary source-CNF equivalence and is analogous to a discrete gauge action; it is not claimed as a new physics or coding-theory theorem.

There are \(2m=14\) literal-incidence polarity bits in this family, and each of the six variables is active. Since distinct variable flips affect disjoint incidence positions, the gauge action is free and has \(2^6=64\) distinct elements per orbit. Fixing the first incidence of each variable to negative polarity gives a unique canonical representative. Therefore:

\[
\#\text{gauge orbits}=2^{2m-n}=2^{14-6}=\boxed{256}.
\]

The code explicitly canonicalized **all 16,384** signings: **256 orbits**, each of size **64**, and their representatives reproduced **all 135** distinct cycle spectra. This can reduce the number of *signing variants to enumerate* by a factor of 64 in future matched experiments. It is **not** a factor-64 speedup for counting assignments to an arbitrary input CNF.

### Source-exact matched witness

Two signings (little-endian polarity bitmasks `2603` and `2607`) have the same exact graph and full energy profile:

```
                 Source A                 Source B
clause 0          ( 1 OR  2)              ( 1 OR  2)
clause 1          (-1 OR  3)              ( 1 OR  3)
clause 2          (-1 OR  4)              (-1 OR  4)
clause 3          (-2 OR -3)              (-2 OR -3)
clause 4          (-2 OR  5)              (-2 OR  5)
clause 5          (-4 OR  6)              (-4 OR  6)
clause 6          (-5 OR -6)              (-5 OR -6)
```

- Both: \((A_0,\ldots,A_7)=(2,22,30,10,0,0,0,0)\), hence **two satisfying assignments**.
- Source A: \((E_0,\ldots,E_7)=(2,12,2,0,0,0,0,0)\).
- Source B: \((E_0,\ldots,E_7)=(2,16,10,4,0,0,0,0)\).

Thus even the *entire* energy distribution does not determine the cycle-parity-conditioned distribution in this finite family. The constant coefficient remains 2 in both, consistent with W-CROSSDOMAIN-008's warning that homogeneous clause-violation parity does **not** change #SAT.

## Independent controls and replicability

- `scripts/benchmark_fourier_signed_controls.py`: deterministic full `16384 * 64` enumeration. JSON includes the finite counts, an explicit matched witness and source clauses, and 24 gauge-transformation controls.
- `tests/test_fourier_signed_controls.py`: asserts the exact group counts above; validates witness parity through an **independent source-literal truth-table function** rather than relying on the spectrum auditor's own implementation.
- **Gauge invariance:** flipping a source variable and the polarity of *every* occurrence is a bijection on assignments. Both energy and triangle-parity spectra must remain unchanged. All **24/24** designated variable-flip controls passed; all signings were independently grouped into 64-element gauge orbits. This controls a specific source-isomorphism effect, not all graph automorphisms.
- `rust/witnora-ve/src/aux_fourier_violation.rs`: Rust test checks both witness polynomials against exact coefficients; native Python-wheel comparison is wired into CI.

## What the result does *not* show

- It does not show the feature predicts SAT hardness, variable-elimination width, runtime, or a new solver-complexity measure.
- The single predeclared triangle parity row is not a proven minimal or optimal representation; graph automorphism, clause indexing, and alternate parity bases need separate tests.
- The 16,384 cases share one graph; larger graph families, randomization controls, adversarial relabelings, and held-out selection are still necessary.
- Cardinality of distinct spectra is not an information-theoretic entropy estimate; the uniform distribution over literal signings and gauge/orbit multiplicities matter.
- We have not measured the Rust Fourier algorithm's performance against a direct XOR-syndrome dynamic program. Rust-native compilation/CI is pending; Python finite controls passed locally.

## Next discriminating test

Replicate matched signings across several non-isomorphic source graphs and different cycle bases, then evaluate how much syndrome spectra predict **measured native solver cost** after matching on \(n\), \(m\), separator size, #SAT, and ordinary energy histograms. The null hypothesis is *no added predictive value*. A positive finding would first be a finite empirical signal, not a mathematical theorem.

## Primary literature

- G. David Forney Jr., **“Codes on Graphs: Duality and MacWilliams Identities,”** *IEEE Transactions on Information Theory* (2011): <https://arxiv.org/abs/0911.5508>.
- A. Al-Bashabsheh and Y. Mao, **“On Factor Graphs and the Fourier Transform,”** *IEEE Transactions on Information Theory* (2005): <https://ieeexplore.ieee.org/document/1424306/>.
- S. Aref, **“A Modeling and Computational Study of the Frustration Index in Signed Networks,”** *Networks* (2020): <https://onlinelibrary.wiley.com/doi/full/10.1002/net.21907>.
