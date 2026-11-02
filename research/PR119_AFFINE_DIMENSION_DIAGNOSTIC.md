# PR #119: Algebraic search-space diagnostic (synthetic, not SATLIB)

Status: **exploratory hypothesis test; original shared experiment unreproduced**.

## Provenance and limitation

A user-supplied [public ChatGPT share](https://chatgpt.com/share/6ae8832f-d310-83ea-ae7b-d45a12607b0f)
describes an earlier Witnora algebraic
branch search that solved 10/10 parity-16 development files in 8.32 CPU s,
then 0/10 untouched parity-32 files under a 4,000-node cap. The share cites
local commits `bc8e3f5` (frozen search) and `23b4dc6` (holdout results).
Neither commit was found in this repository's connected GitHub history or
current local checkout. The referenced scripts and SATLIB data are also
absent. **The earlier results were not independently reproduced here.**

## New diagnostic

`scripts/experiment_affine_dimension_diagnostic.py` generates separate
planted synthetic systems at 16 and 32 Boolean variables. Each case starts
with `n/2` ternary GF(2) equations and `2n` planted-satisfiable clauses.
For five branch steps, it tracks exact GF(2) dimension and the number of
clauses that can still be falsified by some affine-consistent assignment.
Each clause is split into disjoint branches by its first satisfied literal,
and the largest surviving affine branch is retained as a deliberately
difficult continuation. This is **not the missing source search algorithm**.

Eight fixed seeds per size produced the following descriptive averages:

| Metric | 16 variables | 32 variables |
| --- | ---: | ---: |
| Initial free affine dimension | 8.000 | 16.125 |
| Free dimension after five steps | 3.000 | 11.125 |
| Initially unresolved clauses | 26.625 | 62.625 |
| Unresolved clauses after five steps | 5.750 | 37.750 |

The remaining 32-variable affine space is substantially larger despite the
same five steps, suggesting the next study should measure constraint
progress per unit of cost, not simply report branch counts. No claim is made
about the omitted PARITY holdout or other SATLIB benchmarks.

## Independent test oracle

`tests/test_affine_dimension_diagnostic.py` checks GF(2) solution counts
against exhaustive Boolean assignments for 220 small random systems, and
disjoint/exhaustive clause branch coverage for another 220 random cases.
The test suite passes. This validates the diagnostic's finite arithmetic,
not universal algorithmic superiority.

## Next evidence gate

Recover the actual `bc8e3f5` and `23b4dc6` source/result artifacts before
claiming reproduction. Then instrument the frozen search with independent
affine-dimension and unresolved-CNF measurements at each split on both
16-bit development and 32-bit untouched instances, keeping the original
budget and comparing with appropriately normalized native solver limits.
