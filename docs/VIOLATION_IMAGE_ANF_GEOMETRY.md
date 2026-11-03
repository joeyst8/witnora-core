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
