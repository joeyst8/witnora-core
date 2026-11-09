# WU-001 — Parity UIP requires reason provenance

**Status:** finished finite counterexample to a *specific* candidate; frontier
question remains open. **Scope:** theory/diagnostics only. No solver changes,
no benchmark speedup, no claims about complexity classes.

## Origin in established work

Paul Beame and Glenn Sun, *Extending CDCL to Disjunctions of Parity Equations*,
SAT 2026, DOI [10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5),
Definition 3.2 and Algorithms 2–3. Their Proposition 3.8 proves that the
learned clause is **asserting**; Section 8 explicitly leaves open whether the
algorithm is genuinely analogous to the *first unique implication point* and
how semantic clause minimization should work for disjunctions of affine
equations. The 2026 implementation Xorcle already handles CDCL(⊕); WU-001 does
not present that as new.

## Rejected candidate H0

> The sequence of affine quotient ranks between the falsity space of a
> conflict clause and the prefixes of its unit trail suffices to recover a
> uniquely defined 1-UIP (hence is a basis-free substitute for the implication
> graph).

An affine equation `a·x=b` is stored as the row `(a,b)` over GF(2). An XNF
clause `C` is a disjunction of such equations; negating each disjunct gives
the affine falsity system `F`. Given a consistent prefix `U`, if `U∪F` is
inconsistent then `U` already satisfies `C`. Otherwise define

    q(U,F) = rank(coefficients(U∪F)) - rank(coefficients(U)).

Then `q=0` means a conflict, `q=1` means `C` implies one affine unit, and
`q>=2` means `C` cannot imply any new affine equation under `U` alone. This
is a rephrasing of the established unit-propagation semantics in the cited
paper, **not** a new result. It is invariant under replacing generators by
any invertible row combination.

## Exact finite counterexample to H0

Both runs start from the decision `a=1`, propagate `b=1`, propagate `c=1`,
and conflict on the **same** clause `¬b ∨ ¬c`.

| Trace | Reason for `b=1` | Reason for `c=1` | First UIP |
| --- | --- | --- | --- |
| A (chain) | `¬a ∨ b` | `¬b ∨ c` | `b` |
| B (fork) | `¬a ∨ b` | `¬a ∨ c` | `a` |

These clauses are ordinary CNF, embedded as singleton-parity-disjunct XNF.
The conflict's falsity system is the same in both traces: `F={b=1,c=1}`.
The exact rank signature at trail prefixes `∅`, `{a=1}`, `{a=1,b=1}`,
`{a=1,b=1,c=1}` is **`[2,2,1,0]`** for both traces.

But implication paths differ:

- In A, every path from `a` to contradiction passes through `b` (`a→b→⊥`
  and `a→b→c→⊥`); the closest common node to the conflict is `b`.
- In B, there are paths through `b` and `c` independently (`a→b→⊥` and
  `a→c→⊥`); only the decision `a` is common to both.

An independent signed-literal resolution check reaches the corresponding
**different learned clauses**: A resolves on `c` and learns `¬b`; B resolves
on `c`, then `b`, and learns `¬a`. Each is asserting at backjump level 0.

Thus **identical affine subspaces at every trail prefix and an identical
conflict clause can have different classical first UIPs** when the reason
clauses differ. It is impossible to reconstruct the true UIP from this rank
signature alone. This is a simple counterexample within classical CNF;
its value is as an explicit falsification of WU-001 H0, **not a new theorem**.

### Independent checks

Rust diagnostic: `rust/witnora-ve/src/bin/wu001_parity_uip_falsifier.rs`.

```bash
cd rust/witnora-ve
cargo test --bin wu001_parity_uip_falsifier
cargo run --release --bin wu001_parity_uip_falsifier
```

Four tests check the exact witness (both graph dominators and the independent
resolution trace), all six ordered bases of the same
two-dimensional falsity span, affine consistency cases, and 4,000 fixed-seed
row systems against an independent explicit **equation-span** oracle
(enumerates subsets of equations, not Boolean variable assignments).

## Frontier direction H1: reason-aware, basis-independent dominators

The failed H0 isolates missing information: **which inference caused a
subspace increase**, and which earlier subspaces each inference required.
The next hypothesis is deliberately narrower:

> It may be possible to define a *subspace-valued* dominator on the causal
> hypergraph of valid CDCL(⊕) reasons, invariant under equivalent changes of
> equation basis, whose restriction to ordinary CNF agrees with graph 1-UIP
> and which produces an asserting Res(⊕)-checkable cut.

This is **unproven and may fail**. A single equation is not the right
primitive unless reason/decision labels break the GL(k,2) symmetry: for
an unlabeled rank-2 vector space, the automorphism group permutes the three
nonzero vectors transitively, so no nonzero vector is invariant under all
automorphisms.

**Falsification gates for H1:**

1. Define the causal hyperedges using actual sound affine deduction witnesses,
   and prove invariance under changing the displayed basis of every XNF clause.
2. On a finite CNF subset, recover classical graph 1-UIP exactly. A single
   disagreement refutes the claimed generalization.
3. On small non-CNF XNF instances with multiple inequivalent deduction
   witnesses, test whether a unique subspace dominator exists. If not, report
   a *counterexample*, not a weaker redefinition called 1-UIP.
4. Only after passing these gates, seek an independently checkable
   strengthening/minimization proof and benchmark cost against Xorcle.

**Research integrity:** WU-001 does not solve the open 1-UIP question, does
not establish novelty, does not claim a speedup, and does not provide an
algorithm for arbitrary-SAT polynomial time. Negative findings remain useful
because they prevent work on rank-only heuristics from being misrepresented
as first-UIP theory.
