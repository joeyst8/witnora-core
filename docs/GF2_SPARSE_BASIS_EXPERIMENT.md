# Sparse GF(2) row-basis operator: exact parity reduction without dense replacement rows

**Witnora 2026-11-03 · draft PR #121 · pending CI**

This experiment follows [the actual polynomial contraction pilot](EXACT_TENSOR_COUNTING_PILOT.md),
where naive auxiliary polynomial counting took more time/memory than
direct source-CNF counting. The goal is a sound algebra-aware operator
that can remove unnecessary parity factors before contraction.

## Operator

Given a matrix H of parity rows over m clause-violation bits,
choose a linearly independent **subset of the ORIGINAL rows**. Unlike
ordinary reduced row-echelon form, this selection never widens a row;
all retained factors have exactly the original clause IDs and at most
the original configured row-width cap.

The Python constructor `build_sparse_parity_basis` returns:
- Source sketch clause count and original row count.
- Original row IDs selected as independent basis equations.
- A bitset of retained-row coefficients for **every** original row.
- Rank and nullity (= m - rank).

For each original row R_i, a separate checker reconstructs R_i
by XORing the chosen basis rows listed in its coefficient bitset.
It also rechecks linear independence of retained rows. Since every
retained row was itself an original row, this proves the row
satisfaction equivalence for every violation vector:

    H v = 0   ⇔   B v = 0,

where B contains the retained independent rows. This statement
holds for all v; it does **not** establish that an arbitrary H
captures source CNF satisfaction exactly.

The Lean module `GF2RowParity.lean` proves a universal concrete
Boolean-mask lemma: the parity of a pointwise XOR of two row masks
equals the XOR of their individual parities, under equal-length
masks. It also proves the corresponding reversible row replacement
equivalence. These are the algebraic steps underlying basis
compression; checking each Python certificate in Lean remains a
separate production integration task.

## Exact-counting experiment

`exact_tensor_counting.py` can accept a basis **only after**
independently verifying its reconstruction against the exact input
sketch. This protects source identity and row-space equivalence.

The controlled experiment measures the **full auxiliary polynomial
Z_H(t)** on small instances, comparing original row factors and
certified reduced row factors, under identical memory/scope budgets.
The polynomial (not merely the SAT constant term) must remain
identical for any correct basis.

A four-unit-clause adversarial sketch is included, with six original
degree-3 sparse checks on four violation bits and a 1-dimensional
nullspace, so the full polynomial is `1 + t^4`. This tests the
critical distinction between preserving parity acceptance and
incorrectly claiming source-CNF exactness.

Larger 32/224, 96/576 and 256/1536 benchmarks measure ONLY row
construction, verification, rank and nullity. They do **not** perform
SAT/counting at those sizes.

## Go/no-go criterion

A true practical improvement requires lower **total exact counting
time and memory**, not merely fewer rows. Removing redundant rows
can only help if the retained factors also admit a favorable
contraction order. An independent sparse basis is mathematically
exact, but no general efficient SAT/#SAT or polynomial-time claim
follows from Gaussian elimination alone.

Numerical results and CI status will be appended after verification.


## Verified outcome: sparse GF(2) row-basis counting experiment

[General-resolution CI run #41660196196](https://github.com/joeyst8/witnora-core/actions/runs/41660196196)
passed the new Lean module `GF2RowParity`, five Python
GF(2) basis/reconstruction tests, exact contraction comparisons,
and the existing general-CNF RUP/Glucose/Lean regressions.
Lean reports only standard axioms
`[propext, Classical.choice, Quot.sound]` for the two row-operation
theorems; no `sorry` or new project axiom was introduced.

In the small cases, the exact polynomial was **identical** before
and after basis compression:

| Case | Original rows | GF(2) rank / rows retained | Original exact polynomial contraction ms | Reduced ms | Full polynomial |
|---|---:|---:|---:|---:|---|
| Four-unit-clause collision | 6 | 3 | 1.391 | 1.141 | `1+t^4` |
| 4v/5c planted | 6 | 5 | 4.727 | 4.086 | exact same constant |
| 5v/7c planted | 5 | 5 | 27.755 | 28.063 | exact same constant |
| 6v/9c planted | 8 | 8 | 71.520 | 70.147 | exact same constant |
| 8v/12c planted | 12 | 11 | **BUDGET_EXCEEDED** | **BUDGET_EXCEEDED** | not computed |

These are single-run, tiny Python timings **including basis
certificate verification during the reduced counting call** but not
basis construction outside the contraction timer. They are not
industrial SAT/#SAT or asymptotic measurements. For 8v/12c both
paths failed closed at bucket size12 over configured cap11.

Large non-enumerative **construction only** (no SAT/counting):

| 3-CNF | Source clauses | Original parity rows | Sparse-basis rank | Parity-kernel nullity m-rank | Basis construction/verification ms |
|---|---:|---:|---:|---:|---:|
| 32v/224c | 224 | 150 | 150 | 74 | 1.264 |
| 96v/576c | 576 | 385 | 385 | 191 | 7.151 |
| 256v/1536c | 1536 | 1,022 | 1,021 | 515 | 51.401 |

The sparse-basis algorithm detects nearly **no redundant rows**
in these larger geometry-aware random constructions. Thus a
rank-redundancy-only strategy cannot significantly accelerate
this family. Note the 256-variable nullity 515 describes the
linear violation-bit space, **not** a count of realizable CNF
violation patterns or the number of source models.

### Next mathematical obstacle

The row-space reduction is exact for all violation vectors, but
the original source-CNF map x ↦ v(x) is nonlinear. Better progress
requires exploiting the structure of **realizable** violation
vectors and low-degree clause polynomials, or designing a new
rank-growth/checker operator with explicit proof certificates.
Merely dropping dependent rows is a bounded optimization.
