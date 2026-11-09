# WU-002 — A non-CNF reason exposes coordinate-graph gauge dependence

**Status:** finite falsification completed, 4 Rust tests passed. **Claim
boundary:** This refutes a *naive graph-construction hypothesis* in our
research, not the 2026 CDCL(⊕) algorithm or the unresolved semantic parity
1-UIP problem. No SAT speedup, no new complexity bound, no P-vs-NP claim.

## Established-paper anchor and the unknown

Paul Beame and Glenn Sun, *Extending CDCL to Disjunctions of Parity Equations*,
SAT 2026, DOI 10.4230/LIPIcs.SAT.2026.5, Definitions 3.2 and 3.7, Algorithms
2 and 3, and Section 8. Their Algorithm 3 is proven **asserting**; they
explicitly do not establish a fully generalized graph-theoretic 1-UIP cut.

WU-001 showed that rank profiles fail to retain reasons. WU-002 tests the
natural repair: reconstruct causal edges by expressing each parity reason in
the ordered trail basis, linking an older equation to the new one whenever
it appears in those expressions. The repair is an attractive algebraic
translation of a Boolean implication graph, but it has a hidden choice:
which *equivalent equation* to record as the propagated row.

## Candidate H2, now falsified

> A coordinate-support dependency DAG on an independent affine trail gives
> a first-UIP node invariant under replacing a newly propagated equation by
> that equation plus a previously known true equation.

Our exact XNF input has Boolean variables `a,b,c,d` and **identical reason
clauses in both runs**:

1. Decide `a=1`.
2. Propagate `b=1` from `¬a ∨ b`.
3. Propagate `d=0` from `¬b ∨ ¬d`.
4. Apply the genuinely non-CNF XNF reason
   **`(c⊕d=1) ∨ (b⊕c⊕d=0)`**.
5. Conflict on `¬b ∨ ¬c`.

The non-CNF reason has falsifying affine equations
`F_c={c⊕d=0, b⊕c⊕d=1}`, whose sum is `b=1`. Thus when `b=1` is already
true, the reason reduces to the unit `c⊕d=1`. With `d=0` already true,
this can be represented as `c=1`. Crucially, the clause is semantically
equivalent to `¬b ∨ (c⊕d=1)`; it does **not** simplify to a single CNF clause
on the original variables.

Under the known `a=1`, these are two **equally legitimate** propagated units:

- Trace A records `c=1`.
- Trace B records `h=(c⊕a=0)`, since `h=(c=1)⊕(a=1)`.

The true-unit spans after each prefix are identical in the two traces:
`span(a)`, `span(a,b)`, `span(a,b,d)`, then
`span(a,b,d,c)=span(a,b,d,h)`.

### Observed coordinate graph

| Property | Trace A | Trace B |
| --- | --- | --- |
| Propagated row | `c=1` | `c⊕a=0` |
| Parents of new row from reason coordinates | `b,d` | `a,b,d` |
| Parents of terminal conflict | `b,c` | `a,b,h` |
| Naive graph's first UIP | `b` | `a` |

The difference is a bookkeeping artifact. For example, in trace B the true
equation `c=1` appears as `(c⊕a=0)⊕(a=1)`, so a coordinate graph invents a
direct edge from `a` to the conflict even though the original clause is
unchanged. Every graph edge is algebraically correct *for its chosen basis*,
but the reported first UIP is not invariant. **H2 is false.**

The executable check covers **all eight** representatives of the form
`c + αa + βb + γd` for `α,β,γ∈{0,1}` (the four earlier-unit combinations
over GF(2)). Four representatives report `b` and four report `a` as their
coordinate-graph first UIP, despite identical prefix subspaces and reasons.

## What survived H2

Let `P=span(a=1,b=1,d=0)` be the true prefix and
`F=span(c⊕d=0,b⊕c⊕d=1)` be the reason's falsity space. Their intersection is

    K = F ∩ P = span(b=1).

Why exact? The input spans have dimensions two and three, their combined
span has dimension four, so their intersection has dimension `2+3−4=1`; `b=1`
belongs to both. This subspace remains unchanged in both traces and under
all six invertible generator pairs for `F`. The *quotient* `F/K` is
one-dimensional. This pair `(K,F/K)` is a **basis-independent reason
descriptor**, but it has **not** been proven sufficient to determine a
unique parity 1-UIP or to produce valid minimized learned clauses.

### Reproducibility

Rust diagnostic: `rust/witnora-ve/src/bin/wu002_reason_gauge.rs`.

```bash
cd rust/witnora-ve
cargo test --bin wu002_reason_gauge
cargo run --bin wu002_reason_gauge
```

Four tests verify the two displayed propagation representatives and graph
dominators, all eight legal affine row representatives, the exact invariant
intersection, all six ordered generator bases, and 2,000 deterministic
independent row-coordinate reconstructions.
All linear operations use GF(2) elimination; no Boolean assignment
enumeration is used.

## Next frontier question (WU-003, open)

> Is there a **subspace-valued dominator** defined on the causally labeled
> affine deduction process, using the quotient reason `(K,F/K)` rather than
> individual row coordinates, which (i) is invariant under equivalent
> propagations, (ii) recovers classical 1-UIP on CNF input, and (iii)
> admits a polynomial-size Res(⊕) verification certificate?

Before any implementation claim:

1. Formally specify what it means for a subspace to intercept *all*
   reason-preserving refutations; do not equate rank one with graph dominance.
2. Check CNF conservativity on exhaustive small reason graphs and XNF
   invariance against all legal basis changes for fixed 3–5-variable cases.
3. Search adversarial examples where two distinct witness decompositions
   create incomparable candidate dominator subspaces. One such witness
   refutes uniqueness.
4. Only if this survives, define and independently verify a learned
   Res(⊕) clause and benchmark against published Xorcle.

**Novelty check:** No assertion of an original literature result. The value
of WU-002 is a reproducible *local no-go test* preventing a basis-dependent
algorithm from being described as a basis-independent first-UIP method.
