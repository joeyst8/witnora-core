# W-CROSSDOMAIN-024: a frozen second-vs-third-order information barrier

Status: prospective, committed **before** the first W024 Rust experiment.

## Scientific question

W023's deflated spectrum largely replicated a cheap polarity statistic.
Can there exist SAT and UNSAT formulas with **identical** variable
degrees, positive/negative counts, unsigned clause hypergraph,
signed clause-length histograms and *all signed pairwise Gram moments*,
but distinct satisfiability? If so, what higher-order information
is necessary to distinguish this pair?

This is an intentionally **constructed counterexample class**. We
do not claim an unrestricted lower bound, universal novelty, solver
speedup, or a proof of P versus NP. XOR recognition plus GF(2)
elimination is established SAT mathematics; W024 tests the expressive
limit of Witnora's particular second-order statistics.

## Five 3-XOR source equations on nine variables

Use five distinct triples in this fixed order:

`(1,2,3), (1,4,5), (2,4,6), (3,5,6), (7,8,9)`.

The first four XOR left-hand sides sum to zero over GF(2); the fifth
is an independent component. Two right-hand-side patterns:

- **SAT**: `(0,0,0,0,1)` — the independent equation is odd.
- **UNSAT**: `(0,0,0,1,0)` — one equation in the dependent cycle is odd.

For each equation, encode its 3-XOR into exactly four 3-literal CNF
clauses, one for each forbidden parity assignment. Thus **both**
formulas have nine variables, 20 clauses, and 60 literal occurrences.
Each occurrence triple has all four sign combinations of a fixed
product parity, giving *two positive and two negative occurrences per
participating variable*, independently of the XOR RHS.

Both formulas contain exactly four even-XOR blocks and one odd-XOR
block, so even the **global histogram of clause negative-literal counts**
is matched. The variable-triple multiset is exactly the same.

## Exactly 64 paired relabeling controls

Use xorshift32 with seed `0xD24F0240 ^ ((index+1)*0x9E3779B9)` for
indices 0 through 63, a Fisher–Yates permutation of variables `1..9`
and one Fisher–Yates shuffle of 20 clause positions. **Apply the
same transformations to both sides of each pair.** No gauge flips
in the primary matched experiment because they can change the global
negative-literal histogram. These 64 pairs are **isomorphic relabelings
of one underlying pair**, not 64 independent samples.

## Preregistered tests and signals

For every pair, compute from actual clauses—not generator metadata:

1. Exact SAT truth using all `2^9 = 512` assignments, independently
   per side; require SAT vs UNSAT.
2. Positive/negative variable degrees, sorted unsigned triple counts,
   global number-of-negative-literals histogram, and the integer
   signed Gram matrix `G_ij=sum over clauses s_i(c)*s_j(c)` (zero
   when variables do not co-occur). Require every one of these
   statistics to be **identical** across the pair.
3. Verify each Gram off-diagonal equals zero and every diagonal
   equals its variable occurrence count. With fixed width 3, the
   normalized W022/W023 `B^T B` must therefore be exactly `I/3`
   on all nine variables: no nontrivial second-order spectrum.
4. Recover XOR equations from the **source clauses** by grouping
   identical variable triples, verifying all four distinct forbidden
   sign patterns, and reading the triple sign product. Use source-
   indexed GF(2) elimination to identify a true inconsistent cycle,
   and independently validate the combined equation mask 0 and RHS 1.
   It should return SAT for the one independent odd equation and UNSAT
   for the one dependent odd equation.
5. Independent Python controls for indices `0,1,31,63` must reconstruct
   source clauses, run exhaustive truth, audit every matching statistic
   and the XOR outcome without trusting Rust's reported decision.

Complete the benchmark in **Rust**; Python is limited to independent
verification. Archive all controls, both outcomes, and any failed case.

## Interpretation if successful

The result would prove a **restricted representation limitation**:
no function of this deliberately specified collection of first-
and second-order statistics can classify both members of the pair.
Triple-specific sign moments plus GF(2) dependencies distinguish them.
This is a basic XOR parity phenomenon, closely related to existing
Fourier/XOR reasoning; not a new general SAT complexity theorem.

Relevant literature: established CDCL/XOR integration and complete
parity reasoning, e.g. https://arxiv.org/abs/1207.0988.
