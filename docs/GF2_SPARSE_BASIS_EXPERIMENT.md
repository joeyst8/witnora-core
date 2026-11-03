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
