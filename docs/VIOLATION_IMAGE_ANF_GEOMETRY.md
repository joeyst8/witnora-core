# Violation-image geometry: symbolic low-degree ANF parity constraints

**Witnora, 2026-11-03 · draft PR #121**

This experiment follows the [sparse GF(2) row-basis
frontier](GF2_SPARSE_BASIS_EXPERIMENT.md). Almost every parity row
was independent on the large 256/1536 frozen case, so eliminating
redundant checks cannot by itself reduce the nonlinear counting burden.

We now represent the exact map from source assignments to clause
violations symbolically, without enumerating source assignments.

## Exact Boolean-ring construction

For source bit x_v in {0,1}, the false-indicator for a signed literal
is the Boolean-ring polynomial

    False(+v) = 1 + x_v
    False(-v) = x_v

over GF(2), where x_v² = x_v on Boolean assignments.

The violation bit of a source clause C_j is exactly

    V_j(x) = PRODUCT_(lit in C_j) False(lit).

For 3-CNF each V_j is multilinear and has degree at most three;
the product automatically simplifies duplicate literals and
tautological pairs, e.g. V([x, -x]) = 0.

For a parity row R_i selecting source clause IDs,

    P_i(x) = XOR_(j in R_i) V_j(x).

This is a nonlinear polynomial constraint in source variables alone.
It exactly equals the parity of the clause-violation bits for every
source assignment. Equal monomials cancel modulo two.

The implementation `witnora_core/violation_image_anf.py` uses
canonical sets of variable-ID monomials, with symmetric difference
for XOR and set union for idempotent Boolean-ring multiplication.
It outputs concrete polynomial equations and counts terms, degrees,
distinct equations and cancellations without enumerating assignments.

## Formal trust boundary

New Lean module `formal/Witnora/ViolationProduct.lean` proves
the universal signed-clause identity:

    NOT(ANY literal true) = PRODUCT(ALL literal false),

for every clause and assignment, and hence source
`violationVector` equals the list of product indicators.

This is a semantic ingredient of the ANF construction; the
complete Python monomial data structure and normalization routine
have not yet been formally refined into Lean. Tests independently
compare the Python ANF evaluator against the existing signed-literal
violation evaluator on finite cases.

## Actual bounded count, separate from construction

The small experimental solver uses Shannon substitution,
`x_v=0` and `x_v=1`, and memoization on canonical systems
to count solutions of Boolean polynomial equations exactly.
It can count either

- common zeros of each original clause violation V_j(x), yielding #SAT;
- common zeros of parity polynomials P_i(x), yielding the number of
  source assignments surviving the parity sketch.

These quantities **need not be equal**, because an inexact sketch
can accept nonsolutions. An adversarial four-clause collision is
tested explicitly. Every nontrivial symbolic search is bounded
by an explicit maximum number of states and fails closed rather
than returning an unsupported answer.

This solver may be exponential; it is not a new polynomial SAT
method and is not equivalent to a production CDCL solver.

## What is measured

Small controlled 4/5, 5/7, 6/9 planted 3-CNFs and frozen 8/54,
10/66 SAT/UNSAT examples use exact symbolic counting with separate
small-instance exhaustive oracles. Larger 32/224, 96/576,
256/1536 cases measure **symbolic construction only**:
terms before and after XOR cancellation, max degree, repeated
equations and build time. No large SAT solving is attempted.

The deciding benchmark is whether symbolic cancellation plus
memoization reduces actual counting time and memory relative to
the same solver applied directly to clause violation equations.
Simply shrinking the expression is insufficient.

Numerical measurements and CI status will be appended after
verification. No completion of general-purpose SAT or P vs NP
is claimed.


## Verified results (2026-11-03)

[Full CI run #41669844135](https://github.com/joeyst8/witnora-core/actions/runs/41669844135)
passed the universal Lean signed-clause product lemmas, five
symbolic ANF tests, the actual bounded counting benchmark,
and previous general-CNF Lean/CDCL regressions.

Lean kernel output:
- `falseProduct_eq_not_any` depends on standard `[propext]`.
- `productViolations_eq_violationVector` depends on
  standard `[propext, Quot.sound]`.
No project-specific axiom or `sorry` remains in this module.

### Exact small counting with the same symbolic search algorithm

| Frozen source | Source ANF exact count ms | Parity ANF survivor count ms | Exact answer |
|---|---:|---:|---:|
| 4v/5c planted | 0.443 | 0.879 | 8 |
| 5v/7c planted | 0.726 | 1.031 | 13 |
| 6v/9c planted | 1.357 | 1.391 | 27 |
| 8v/54c UNSAT | 5.863 | 7.265 | 0 |
| 8v/54c planted SAT | 5.237 | 10.024 | 1 |
| 10v/66c UNSAT | 14.584 | 20.896 | 0 |
| 10v/66c planted SAT | 12.346 | 18.724 | 1 |

Each source count matched an independent exhaustive
small-instance model oracle. Each parity count matched the
independently evaluated number of sketch-surviving assignments.
On these frozen examples, the geometry-aware sketch happened
to be exact; the prior adversarial collision test separately
shows this is **not universal**.

These are single-run prototype Python wall times for
Shannon/memoized ANF equation counting, with `max_states=10,000`.
They are **not** industrial SAT solver benchmarks, and do not
include source generation in the timing. In some cases parity
used fewer states (8v/54c UNSAT: 17 vs 34) but took longer
because each nonlinear state was more expensive to simplify.

### Symbolic construction, no assignment enumeration

| Frozen planted 3-CNF | Rows | Raw monomial occurrences | Reduced ANF occurrences | Reduction | Max degree | Build ms |
|---|---:|---:|---:|---:|---:|---:|
| 32v/224c | 150 | 2,502 | 2,118 | 15.3% | 3 | 2.436 |
| 96v/576c | 385 | 6,492 | 5,896 | 9.2% | 3 | 6.593 |
| 256v/1536c | 1,022 | 17,286 | 15,856 | 8.3% | 3 | 19.229 |

No zero or duplicate nonzero ANF row appeared on any of
these three large constructions. Exact counting was **not**
attempted for large n.

For smaller frozen controls, cancellation was stronger
(e.g. 8v/54c planted: 600→364; 10v/66c planted: 708→498)
but still did not make parity-ANF counting faster than
source-clause ANF counting.

### Decision

This closes a useful semantic bridge: the low-degree
source-to-violation polynomial map can be built without
enumerating assignments, and Lean verifies the underlying
clause-product meaning. But term cancellation alone does
not reduce observed counting time. The next operator should
use shared subexpression structure, compiled polynomial
evaluation or elimination, variable-order selection and
independent total-cost comparisons. A universal
Python-monomial-to-Lean refinement remains unfinished.


## Cached-cofactor and component-split counting (2026-11-03 continuation)

New implementation: `witnora_core/anf_structured_counter.py`,
validated by `tests/test_anf_structured_counter.py` and measured in
`scripts/benchmark_anf_structured_counter.py`.

The alternative exact counter compiles ANF monomials into integer
variable-bit masks. Cofactor polynomials under `x_v=0/1` are cached
across search states. The counter also propagates unit ANF equations,
eliminates unconstrained variables as a power-of-two factor, and
detects disconnected equation-variable hypergraph components.

For disjoint equation components `E1` and `E2` with variable
scopes `V1` and `V2` (and free variables `U \\ (V1 ∪ V2)`),
the model count satisfies the exact identity

    #Z_U(E1 AND E2)
      = 2^(|U \\ (V1 ∪ V2)|) * #Z_V1(E1) * #Z_V2(E2).

The identity is valid only when components have disjoint variable
supports; it does not suppose that a dense CNF has small separators.
The separate Lean module `formal/Witnora/ANFComponentFactor.lean`
formalizes the universal count-product rule for independent Boolean
predicates. Full refinement of the Python component detector and
bit-mask compilation into Lean is not yet established.

### Measured exact counts, median of three timed runs

The old and new counters saw **identical** equation systems and
independent reference counts were exercised by Python tests.
Wall times include Python `tracemalloc` instrumentation; each
nontrivial search was limited to 5,000 unique states.

| Frozen system | Old source count ms | Structured source count ms | Old sketch survivor ms | Structured sketch survivor ms |
|---|---:|---:|---:|---:|
| 4v/5c planted | 0.646 | 0.744 | 0.772 | 0.767 |
| 5v/7c planted | 1.249 | 1.192 | 1.760 | 1.663 |
| 6v/9c planted | 2.168 | 1.838 | 2.459 | 2.638 |
| 8v/54c UNSAT | 10.053 | 5.474 | 11.792 | 7.898 |
| 8v/54c planted | 8.659 | 4.831 | 16.465 | 8.887 |
| 10v/66c UNSAT | 15.675 | 8.735 | 34.348 | 13.846 |
| 10v/66c planted | 20.442 | 9.113 | 28.381 | 20.616 |

The structured solver improves most of these frozen cases,
but is marginally slower on the 4v/5c source and 6v/9c sketch.
Even after optimization, dense-case parity sketches were generally
more expensive to count than their source clause systems.

### Separability stress test, no source/sketch conflation

Each 6-variable block has exactly 27 satisfying assignments.
The blocks share **no variables**, and the count is the product.

| Construction | Old source-ANF counter | Structured source-ANF counter |
|---|---|---|
| 3 disjoint blocks (18 variables) | 19,683 models; 3,960 states; 525.779 ms; 6,130 KiB | 19,683 models; 64 states; 7.226 ms; 84 KiB |
| 4 disjoint blocks (24 variables) | Exceeded 5,000-state bound | 531,441 models; 85 states; 9.848 ms; 105 KiB |

The 18-variable disjoint case is approximately 73× faster,
but the benefit comes from **explicit component independence**.
This is a valuable operator for decomposable formulas, not evidence
for polynomial-time counting on arbitrary connected 3-SAT.

The six new unit tests passed, as did the counter comparison and all
earlier Lean/CDCL regression steps in
[CI run #41681763613](https://github.com/joeyst8/witnora-core/actions/runs/41681763613).
The separate Lean factorization proof is CI-gated in a subsequent commit.
Next priorities: confirm that Lean proof, measure separators with
small overlaps (conditioning / component reformation),
separately benchmark SAT/#SAT against independent solvers,
and retain a strict TC-063 restricted-family/general-CNF distinction.
