# W-CRC-018: Graph-, clause-, and model-count-matched semantic controls

Status: **101 green Python tests**, **10/10 exact Witnora model counts**
matching independent Ganak 2.8.0, **4/4 exhaustive small-n semantic
profiles**, and one exact higher-order counterexample, verified in
the full W-CRC regression CI and the completion-driven queue.

Full green W-CRC CI:
https://github.com/joeyst8/witnora-core/actions/runs/41725616948

Verified completion-driven queue:
https://github.com/joeyst8/witnora-core/actions/runs/41725603426

## Why W-CRC-017 was not enough

W-CRC-017 showed that four signed 2-CNF families had the same
complete primal K_n graph, but different model counts and solver
behaviors. Yet their **clause counts also differed**, and model
counts differed. This experiment removes both objections.

For every n in {8,12,16,32,64}, construct two signed CNFs with:

- Exactly n variables and the same **complete K_n primal graph**.
- Exactly **n(n-1) clauses**, two on each pair {u,v}.
- Exactly **2 satisfying assignments**.
- Different model-distribution geometry.

### Family A: pairwise parity

Every pair u<v receives the complete 2-clause encoding of
`x_u XOR x_v = p_u XOR p_v`, for a seeded bit pattern p.
All variables must equal p simultaneously or all its bits are flipped.
The **two** solutions differ at **all n variables**.

Under the uniform distribution over the two solutions, each bit
has both values and **all n(n-1)/2 pairs are dependent**
(positive or negative correlation depending on p).
No variable is a backbone variable.

### Family B: pairwise forcing

Every pair u<v receives `(x_u OR x_v)` and
`(x_u OR NOT x_v)`. The elementary consensus identity

`(A OR b) AND (A OR NOT b) = A`

means that each pair forces x_u = TRUE. Thus
x_1,...,x_(n-1) are all fixed; x_n alone is free.
Exactly **two** assignments satisfy the full source formula,
but they differ in **only one bit**.

Since all other variables have zero variance, every pair is
independent in the (degenerate) uniform model distribution.
There are **n-1 backbone variables**, one live variable and
**zero pairwise dependent pairs**, even though the syntactic
primal graph is K_n.

The two sources are not matched for every feature (e.g. signed
literal distribution and CNF unit-resolution closure). Both
are deliberately easy, structured examples; no inference about
the runtime difficulty of arbitrary #SAT follows.

## Source-checkable exact small-n diagnostic

`scripts/benchmark_crc_matched_semantics.py` enumerates all
assignments **only for n<=12**, validates each clause against
the complete source, then counts the pair table
N00, N01, N10, N11 over satisfying assignments. For a
nonempty model distribution, independence is **exactly**

`N00*N11 - N01*N10 = 0`.

A nonzero determinant witnesses pairwise dependence.
This is a familiar probabilistic independence identity, not
a new complexity invariant. The diagnostic intentionally
rejects n>14 rather than pretending to scale.

Unit tests also verify small cases with an independent exhaustive
model counter, reject UNSAT as having no uniform solution
distribution, and check invariance to clause order and duplicates.

| n | Primal edges | Clauses in each | Solutions in each | Parity live/pair dependencies | Forcing live/pair dependencies |
|---:|---:|---:|---:|---|---|
| 8 | 28 | 56 | 2 | 8 / 28 (exhaustive) | 1 / 0 (exhaustive) |
| 12 | 66 | 132 | 2 | 12 / 66 (exhaustive) | 1 / 0 (exhaustive) |
| 16 | 120 | 240 | 2 | 16 / 120 (analytic) | 1 / 0 (analytic) |
| 32 | 496 | 992 | 2 | 32 / 496 (analytic) | 1 / 0 (analytic) |
| 64 | 2016 | 4032 | 2 | 64 / 2016 (analytic) | 1 / 0 (analytic) |

At n=4,8,10 the separate unit tests likewise confirm exact
model count two, same graph and clause count, plus the distinct
semantic profiles. The benchmark's four exhaustively enumerated
n=8/12 profiles are distinct from its six analytic larger cases.

## Independent Ganak/Witnora counts and performance

**All 10/10 Ganak runs returned 2** and all 10/10 existing
Witnora source/CRC backends also returned 2. The parity family
was handled by the complete-XOR affine source extractor. The
forcing family was handled by the generic exact Shannon backend,
which did not yet apply the simple consensus preprocessing rule.

| n | Witnora parity ms | Witnora forcing ms | Ganak parity engine ms | Ganak forcing engine ms |
|---:|---:|---:|---:|---:|
| 8 | 0.3858 | 1.0632 | 3.4281 | 3.1267 |
| 12 | 0.7731 | 2.5701 | 3.2062 | 3.3678 |
| 16 | 1.4802 | 5.3893 | 3.5998 | 3.3745 |
| 32 | 5.9767 | 36.0421 | 5.0565 | 4.2630 |
| 64 | 30.8950 | 294.8213 | 18.1795 | 6.6130 |

**Negative performance result:** at n=64, Witnora took 294.82 ms
on the forcing family versus Ganak's 6.61 ms reported counting
engine, about **44.6x slower**. This reveals a straightforward
missing preprocessing optimization, not an intrinsically
harder semantic case.

These timings are merely one GitHub-hosted-runner pilot with two
Witnora repetitions, one Ganak execution, and unmatched
preprocessing/hardware contention. Never read them as a general
solver performance ranking. Ganak's default component cache
has a small probabilistic correctness qualification; analytic
formula derivations and exhaustive small examples provide
separate checks.

## Crucial falsification: pairwise dependence is not enough

A single canonical 3-XOR source `x1 XOR x2 XOR x3 = 0`
has exactly four satisfying assignments. Every variable
is live and **every pair is independent** under the
uniform satisfying distribution: the pair determinant
vanishes for all three pairs.

Yet the triple is constrained: the exact Walsh sum of
`(-1)^(x1 XOR x2 XOR x3)` over its four models is **4**.
The full source primal graph is K3.

This explicitly refutes the tempting claim that a pairwise
semantic dependence graph fully describes constraint
interaction. High-order dependencies are essential,
and general tests of them need exact #SAT marginals, which
are computationally costly absent special structure.

## Interpretation and next experimental gate

A graph-only metric, even supplemented by total clause count
and total number of models, cannot distinguish these two
uniform solution distributions. The exact number of backbone
variables, pairwise support dependencies, and higher-order
Walsh moments can, but computing them generically is itself
potentially hard. No new P-versus-NP statement or useful
polynomial bound is implied.

Promising next gate W-CRC-019: systematically measure
**first nontrivial interaction order** on bounded small
parity/OR controls using the complete normalized uniform-model
Walsh spectrum, with a conditional/unsatisfiable negative
control. Contrast exact exponential enumeration with a
source-checkable affine shortcut on parity systems. Derive
precise complexity limits instead of declaring the statistic
a fast algorithm.

Repository branch: `research/w-crc-001-asymmetric-v1`,
draft PR #122, stacked on TC-063 draft #121.
No formal Lean proof or main-branch file changed.
