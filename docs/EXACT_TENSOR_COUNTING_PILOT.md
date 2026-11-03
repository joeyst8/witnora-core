# Witnora exact factor contraction pilot: computation rather than graph estimates

**2026-11-03 · draft PR #121 · bounded experimental milestone**

Previous experiments measured factor-graph elimination widths,
including the limited min-fill improvement 921→774 for the large
256/1536 auxiliary graph. That diagnostic did not execute any tensor
contraction. This experiment introduces an **actual exact
integer-polynomial factor elimination engine** on small CNFs.

## Two exact computations

For an n-variable source CNF F = ∧ C_j, we construct truth-table
factors for each clause and sum over all source bits:

    Direct(F) = ∑_x ∏_j [C_j(x) is true] = #SAT(F).

For the auxiliary clause-violation representation, each source
assignment determines unique violation bits v_j. In addition to
per-clause linkage factors L_j and sparse XOR parity factors P_R,
we include a weight t^(v_j) for each violation bit:

    Z_H(t) = ∑_(x,v) ∏_j L_j(x,v_j)
                    ∏_R P_R(v_R)
                    ∏_j t^(v_j).

The implementation calculates factor products and sums in the
**exact polynomial semiring Z[t]**, with no floating-point arithmetic.
Its first coefficient satisfies

    coefficient(Z_H, 0) = #SAT(F),

even if a sparse parity sketch admits nonsolutions at positive degree.

The polynomial output (not only its t^0 coefficient) is checked
against an **independent finite assignment enumerator** in small tests.
A deliberately adversarial four-unit-clause parity sketch accepts
a four-violation nonsolution, so the polynomial includes a t^4
term while its constant term remains the exact source count.

## What is measured

`witnora_core/exact_tensor_counting.py` supports general source-CNF
truth tables and arbitrary valid sparse odd-column parity factors.
Each elimination step multiplies only factors that involve the
selected variable and sums over that bit, yielding an exact smaller
factor. The engine records:

- Full factor-build and elimination elapsed wall time.
- Explicit table-assignment visits (arithmetic work proxy).
- Peak number of stored table entries (not actual process memory).
- Python's `tracemalloc` peak allocated KiB during the benchmark.
- Largest encountered intermediate union scope.

Every run has a hard cap on intermediate variable scope and visited
table assignments, and fails closed with `BUDGET_EXCEEDED` when exceeded.
A capped run is **not a solver answer**.

The controlled pilot uses the same independent source models for
both approaches and checks computed counts against explicit finite
enumeration for n≤8. It includes a parity collision counterexample,
small planted 3-CNFs, and growing test instances.

The 256-variable auxiliary graph measured earlier is far beyond the
explicit-table engine's safe range. This pilot does NOT establish
industrial performance, polynomial-time SAT, general exact sparse
parity equivalence, or completion of TC-063.

## Decision criterion

A meaningful improvement must beat **the direct source CNF
contraction's total time and peak memory**, across repeatable instances
and adversarial controls. If the auxiliary polynomial contraction
is slower, we should investigate a new algebra-aware operator
(e.g. direct elimination of parity equations with shared summaries),
not infer speed from compressed equations.

CI and benchmark numerical results are recorded separately after
they are actually observed.
