# Sparse odd-column parity: a nonenumerative construction and a geometric negative control

**Witnora research checkpoint:** 2026-11-03 · draft PR #121.

This is the next step after
[the randomized dense baseline](CONSTRAINT_GEOMETRY_RANDOM_PARITY_BASELINE.md).
It is an original *coding-theoretic diagnostic*, not a reproduction or
validation of OpenAI's full ETH construction.

## A nonenumerative sparse detection theorem

Treat the m original CNF clauses as columns of a binary r×m matrix A.
Construct A so that:

1. Every column contains **exactly three 1s**.
2. No two columns are identical.
3. Every row contains at most w 1s (default **w=5**).

These structural conditions require no SAT assignment enumeration. For any
violation vector v with Hamming weight 1, 2, or 3, we get A v ≠ 0:

- Weight 1: its column is nonzero.
- Weight 2: XOR of two distinct columns is nonzero.
- Weight 3: XOR of three odd-weight columns itself has odd coordinate
  parity, hence is nonzero.

Thus no assignment violating 1, 2, or 3 clauses can pass all parity
checks. This is a general combinatorial argument; structural Python
checks independently validate every produced matrix. **The full
universal theorem has not yet been kernel-proved in Lean**, and no
guarantee is made for violation supports of weight 4 or more.

The constructor `witnora_core/sparse_parity_checks.py`
chooses distinct column signatures using bounded-load randomized
balancing. It never enumerates SAT assignments. It either returns a
matrix satisfying every structural condition or raises an error.
The source is bound by the SHA-256 of the canonical signed-clause list.

## Adversarial negative control: a four-clause collision

The following four degree-three columns are distinct, but XOR to zero:

    c0 = {0,1,2}
    c1 = {0,3,4}
    c2 = {1,3,5}
    c3 = {2,4,5}

Each of the six row indices occurs in exactly two columns, so
c0⊕c1⊕c2⊕c3 = 0. For CNF [[1],[2],[3],[4]], the all-false assignment
violates all four clauses and escapes this parity matrix. Therefore a
guarantee up to weight 3 must **never** be advertised as a general
CNF-equivalence theorem. Our test verifies both the guarantee and the
actual false positive.

## Frozen SAT source results

For the existing six complete-primal Glucose 3-CNF controls, the
nonenumerative sparse constructor generated:

| Variables / clauses | Rows | Max row width | False positives in exhaustive audit |
|---|---:|---:|---:|
| 8 / 54 UNSAT | 36 | 5 | 0 |
| 8 / 54 planted SAT | 36 | 5 | 0 |
| 10 / 66 UNSAT | 43 | 5 | 0 |
| 10 / 66 planted SAT | 43 | 5 | 0 |
| 12 / 84 UNSAT | 54 | 5 | 0 |
| 12 / 84 planted SAT | 54 | 5 | 0 |

Each matrix's 1–3-support guarantee was independently brute-checked
over the *clause support space*, not over SAT assignments. The
assignment audit was performed separately only to measure empirical
collisions on these tiny sources.

The same nonenumerative constructor generated a **349-row**, width-5
matrix for a 96-variable / 576-clause source and a **925-row**, width-5
matrix for 256 variables / 1,536 clauses. Neither large case has a
general source-equivalence certificate, solution count, or solver speed
measurement.

## Does sparse locality actually help counting?

This is the crucial negative result of our new geometric diagnostic.

The `scripts/benchmark_sparse_parity.py` program builds
factor scopes from the original source clauses, the new sparse parity
equations, and the earlier dense random parity equations. It computes
a **minimum-degree elimination width** for each factor graph.
That number is the width of one explicit elimination ordering and
therefore an *upper bound* on optimal treewidth, **not** a proof of
treewidth lower bounds or actual tensor-contraction runtime.

A local diagnostic run (source generators use planted random 3-CNFs)
returned:

| Variables / clauses | Source width | Sparse parity width | Dense parity width |
|---|---:|---:|---:|
| 8 / 54 | 7 | 7 | 7 |
| 12 / 84 | 10 | 11 | 11 |
| 32 / 224 | 26 | 31 | 31 |
| 96 / 576 | 73 | 93 | 95 |
| 256 / 1,536 | 191 | 246 | 255 |

Although every sparse row touches at most five source clauses and
at most fifteen original variables in these 3-CNFs, many such local
interactions can still create an almost complete global factor graph.
The heuristic width grew substantially relative to the original
source in larger cases. **Therefore sparse row width by itself did
not show evidence of easier generic variable-elimination counting.**

This observation changes the next research design: choose parity
checks with *global contraction geometry in mind*, not merely few
clauses per check. Candidate operators include separator-aware
sparsification, shared-variable linear summaries, structured
expander/Tanner checks with controlled graph width, and exact
modular tensor contraction. Crucially, such methods must still
detect high-weight violation patterns or carry a Lean-checkable
certificate proving exactness.

## Status and limits

- Structural detection of violation supports 1–3: mathematically
  justified and exhaustively tested on selected matrices.
- Exactness on six small frozen CNFs: exhaustive finite test only.
- Exactness on larger CNFs: **not established**.
- Universal low-weight theorem in Lean: **open**.
- Fast exact counting / tensor-network implementation: **not completed**.
- Claimed polynomial or subexponential SAT time: **none**.
- Independent industrial SAT speedup: **none**.

The next milestone is a *geometry-aware sparse row selection* that
keeps global contraction width small **and** provides a checkable
high-weight collision exclusion mechanism. No P=NP claim follows.


## CI acceptance and construction-only timings

The 28-step general SAT/Lean gate passed on 2026-11-03:
[GitHub Actions run 41646810807](https://github.com/joeyst8/witnora-core/actions/runs/41646810807).

The new sparse-constructor tests, complete 1–3 support audits,
all six frozen SAT/UNSAT finite audits, adversarial four-bit collision,
tampered-source rejection, 96-variable nonenumeration interception,
and previously verified general-CNF RUP regressions passed.
The new 1–3 coding theorem remains a mathematical argument and
Python-checked structural property, not a new Lean universal theorem.

Single-run GitHub Actions construction measurements (not SAT solving
or counting; hardware-dependent diagnostics):

| Variables / clauses | Sparse rows | Maximum clauses per row | Construction, ms |
|---|---:|---:|---:|
| 8 / 54 | 36 | 5 | 1.039 |
| 12 / 84 | 54 | 5 | 1.931 |
| 32 / 224 | 138 | 5 | 11.179 |
| 96 / 576 | 349 | 5 | 73.618 |
| 256 / 1,536 | 925 | 5 | 551.940 |

The 96-variable and 256-variable transformed systems remain
**unaudited for exactness** and **unsolved**.
