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


## Verified results: first real contraction timings (2026-11-03)

The full general-resolution CI gate completed successfully:
[run #41658295643](https://github.com/joeyst8/witnora-core/actions/runs/41658295643).
The run passed six new exact counting tests, a controlled actual
factor-contraction benchmark, the existing geometry tests, Lean
theorems and all previous general-CNF CDCL/RUP regressions.

These are **single-run Python prototype measurements including
factor construction**, with `max_bucket_variables=11`,
`max_visited_assignments=1_000_000`. They are not optimized
solver benchmarks or evidence of asymptotic behavior.

| Case | Exact #SAT | Source contraction ms | Auxiliary full-polynomial ms | Source/aux peak traced KiB | Auxiliary bucket bits |
|---|---:|---:|---:|---:|---:|
| 3v/3c | 5 | 0.857 | 3.064 | 6.2 / 18.6 | 6 |
| 4v/4c adversarial four-bit collision | 1 | 0.727 | 2.457 | 5.9 / 13.9 | 4 |
| 4v/5c planted | 8 | 1.288 | 8.899 | 8.1 / 28.8 | 7 |
| 5v/7c planted | 13 | 2.259 | 54.447 | 10.5 / 40.3 | 10 |
| 6v/9c planted | 27 | 3.121 | 138.650 | 15.1 / 51.9 | 11 |
| 8v/12c planted | 47 | 5.026 | **BUDGET_EXCEEDED** | 23.4 / 66.7 | would require 12 |

The adversarial 4-unit-clause sketch produced the exact polynomial
`Z_H(t)=1+t^4`: the additional positive-weight nonsolution
does not corrupt the constant coefficient 1. For the other
successfully contracted frozen examples, sparse parity happened
to admit no nonmodels, so the full polynomial was constant.

The largest attempted bridge contraction failed **closed** at
intermediate union scope 12 (> declared cap 11). This is not
an UNSAT or SAT conclusion.

Measured auxiliary/full-polynomial slowdown relative to the
source direct count was approximately 3.6×, 3.4×, 6.9×,
24.1× and 44.4× on completed cases, respectively.
Traced peak KiB is Python `tracemalloc` allocator instrumentation,
not process RSS or a universal lower bound on memory.

### Consequence

The first real compute experiment supports a negative hypothesis:
naive exact polynomial tensor contraction of the auxiliary
violation-bit representation is less efficient than direct
source-CNF factor elimination on these tiny cases. It reveals
a **specific engineering obstruction**, not a complexity lower
bound. We should prioritize a mathematically sound parity-aware
eliminator that can exploit XOR linearity without materializing
general polynomial tables for every auxiliary bit. Re-run against
actual CDCL/#SAT solvers only after such an operator exists.
