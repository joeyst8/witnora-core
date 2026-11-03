# Witnora constraint geometry: non-enumerative parity baseline

Research date: 2026-11-03 UTC · draft PR #121
Branch: `formal/g14-python-seen-enqueue-v121`

This follows the prior [OpenAI ETH clause-parity bridge](OPENAI_ETH_CLAUSE_PARITY_BRIDGE.md).
The earlier greedy sparse experiment found exact 2–5 clause rows by
exhaustively enumerating all Boolean assignments. The new baseline removes
that enumeration from **construction**, at the price of much denser rows.

## Rigorous probability statement, with exact assumptions

For a CNF F with n variables and m clauses, define its violation vector
v_F(x) in F_2^m. Fix the formula F *before* sampling a parity matrix.
Choose an r×m matrix A with all entries independent uniformly random
bits. Let E be the event that some nonsatisfying assignment x satisfies
A v_F(x)=0.

For any fixed v_F(x) ≠ 0, select one nonzero coordinate. Conditioning
on the other entries in each row, the selected coordinate makes the
row's parity perfectly fair. Thus the chance of passing all r rows is
2^(-r). A union bound over at most 2^n nonmodels gives

    Pr_A[E] ≤ 2^n * 2^(-r) = 2^(n-r).

Selecting r=n+s yields failure probability at most 2^(-s), e.g.
s=20 gives at most 1/1,048,576. Every original model always passes.
This proves a randomized **existence/accuracy bound for ideal independent
draws**, NOT a deterministic certificate for any sampled matrix or an
efficient SAT algorithm. Reproducible seeded Python Random results
are only experiments; the formal probability estimate is not a claim
about a particular PRNG seed.

## Implementation and checks

`witnora_core/constraint_geometry.py` constructs r=n+s
source-bound rows using only independently drawn clause-selection
bitmaps. Its builder does not inspect candidate assignments, models,
or violation vectors, and accepts n beyond the finite enumeration
ceiling. `tests/test_constraint_geometry.py` intercepts
the violation-vector evaluator and proves operationally that the
builder never calls it on a 96-variable / 576-clause fixture. It
exhaustively audits the six previously frozen dense CNFs
(8/54, 10/66, 12/84, each UNSAT and planted-SAT): the fixed seed
73 with s=20 produced zero surviving nonmodels on all six.
This is **empirical acceptance of those six matrices only**;
it is not a proof of exactness for all CNFs.

`scripts/benchmark_eth_constraint_geometry.py` reports
construction-only runtime and mean row width at 8, 12, 32, 96
and 256 variables. The n>14 cases are deliberately not audited by
enumerating assignments and have no concrete exactness claim.

The new Lean lemmas in `ClauseViolationParity.lean`
formalize another geometric fact: a row disjoint from all violated
clauses has even parity, and any family of such disjoint rows accepts
the assignment. These are universal collision *mechanism* theorems,
not a formal probability argument or a verified fast algorithm.

## Geometric obstruction for sparse rows

Define the realizable singleton-violation indices

    S(F) = {j : there exists x with v_F(x)=e_j},

where e_j has exactly one 1 at clause j. Any exact parity sketch must
include column j in at least one row for every j in S(F):
otherwise that particular bad assignment passes every check.

If every parity row has width at most w, r rows have at most r*w
selected clause positions. Therefore a necessary condition is

    r >= ceil(|S(F)|/w).

The concrete five-unit-clause family [[1],[2],[3],[4],[5]]
realizes all five singleton violation vectors. With width at most 2,
two rows cannot suffice; at least three are necessary. The Python
tests enumerate all pairs of 1–2-wide rows and independently check
the obstruction. The general cardinal inequality is a paper proof
only for now; its full Lean formalization is a separate obligation.

This gives an operational definition of a dimension of constraint
separation without claiming it equals P-vs-NP complexity.

## The important negative result and the next steps

The random rows are expected to contain m/2 source clauses.
So even though r≈n is a compact **equation count**, the total
incidence count is O(n*m), and the low-degree equations can have
very large variable scope and high tensor contraction width.

A small row count does not imply a fast solver. Our next milestones:

1. Prove and test non-enumerative **sparse** expander-derived checks;
   formally audit coverage against singleton/low-weight obstructions.
2. Produce symbolic degree-at-most-k violation polynomials, with
   Lean-verified correspondence to signed CNF semantics.
3. Implement modular exact model counting on the derived factor graph
   and track contraction width, tensor sizes, memory, and elapsed time.
4. Benchmark source-to-certificate total costs against independent
   CDCL solvers using frozen held-out and adversarial sources.

The performance gate is **total time = construct + count + verify**.
No polynomial-time, subexponential-time, or P=NP conclusion is claimed.
