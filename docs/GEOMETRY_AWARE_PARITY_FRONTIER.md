# Geometry-aware parity: the compression–contraction frontier and a direct-scope no-go theorem

**2026-11-03 Witnora research checkpoint** · draft PR #121
This continues [sparse odd-column parity](SPARSE_ODD_COLUMN_PARITY_GEOMETRY.md).

## New construction

`witnora_core/geometry_aware_parity.py` partitions each source
3-CNF variable's incident clauses into capacity-w buckets. A parity row
is each bucket, so all its clauses share a source variable. Every clause
participates in exactly three rows, one associated with each distinct
variable. If two clauses otherwise get identical column signatures,
a dedicated row splits one incidence and retains structural validity.

Properties structurally verified by the existing sparse checker:
- No SAT assignment enumeration during construction.
- Row width at most w; every column has exactly three nonzeros.
- Column signatures remain pairwise distinct (including duplicate
  variable triples with different literal signs).
- All realizable violation supports of size 1, 2, or 3 are detected,
  by the previously documented odd-column coding argument.
- Full equivalence beyond weight 3 is **not** established in general.

For each variable, candidate buckets minimize new pairwise variable
interactions *relative to the original source primal graph*;
this is a deterministic local heuristic, not an optimal contraction
ordering. It supports only 3-CNFs with three distinct variable IDs.

## Formal no-go: direct union-of-clauses factors cannot erase source edges

Consider the direct factorization where each parity equation has a
variable scope equal to the union of all variables in its selected
source clauses. If every source clause occurs in at least one parity
row, then for every pair of variables co-occurring in a source clause,
there exists a parity factor containing both variables.

Therefore, for this **particular direct representation**,

    PrimalGraph(source) ⊆ PrimalGraph(direct_parity_factors).

Ordinary graph treewidth is monotone under edge addition, so the
*optimal* treewidth of this direct factor graph cannot be lower than
the source primal graph's treewidth. In contrast, the experimentally
computed min-degree elimination width is a heuristic UPPER bound on
treewidth, and need not be monotone across arbitrary instances.

The new `formal/Witnora/GeometryScope.lean` contains
a universal, abstract proof of **source-pair containment** under explicit
clause-coverage assumptions. It does not formalize the graph-theoretic
treewidth monotonicity corollary, and it does not apply to alternate
tensor factorizations with auxiliary shared variables, algebraic
cancellations, or different contraction structures.

This is an important limitation on the naive approach: rearranging
source-clause violation polynomials into flat parity factors
**cannot by itself make the direct primal graph structurally narrower**.
To reduce the hard part of exact counting, we need new internal
representations, not only shorter parity rows.

## Controlled geometry results

The geometry-aware construction passed exhaustive equivalence audits
on the previously frozen 8/54, 10/66, and 12/84 UNSAT and planted-SAT
3-CNFs. No assignment enumeration was used to construct the rows.
The large n=96 and n=256 constructions were not audited for exactness.

On planted random 3-CNFs, the explicitly constructed min-degree
elimination widths were:

| Variables / clauses | Original source | Random sparse, w=5 | Geometry-aware sparse, w=5 |
|---|---:|---:|---:|
| 32 / 224 | 26 | 31 | 30 |
| 96 / 576 | 73 | 93 | 90 |
| 256 / 1,536 | 191 | 246 | 241 |

Thus locality-aware selection improved over randomly balanced rows in
these frozen cases but still worsened the direct factor graph compared
with the original formula. These widths are heuristic diagnostics,
**not** actual tensor-counting times or lower bounds on every solver.

### A concrete compression–connectivity frontier (256/1,536)

| Clauses per parity row (maximum) | Geometry-aware rows | Min-degree induced width |
|---:|---:|---:|
| 1 | 4,608 | 191 |
| 2 | 2,370 | 219 |
| 3 | 1,620 | 232 |
| 4 | 1,254 | 234 |
| 5 | 1,022 | 241 |

The original source has 1,536 clauses and observed width 191.
The width-one parity system essentially repeats each original clause
three times, preserving source interactions but providing no compression.
Packing more source clauses into parity rows reduces the number of
checks while adding interactions that make direct elimination harder.

## Research implication

This is useful negative information: *local row sparsity*, *small
numbers of equations*, and *globally efficient contraction* are
different properties. We should explicitly optimize the full
construction-plus-counting cost, not just the count of parity checks.

The next proposed operator is an **auxiliary-variable tensor bridge**:
assign a separate violation bit to each source clause and encode its
correct relation to the source literals; connect violation bits by the
sparse parity checks without flattening each parity equation into a
union of all source variables. Further explore variable-splitting,
shared summaries, structured contraction, and exact interpolation.

Any such bridge needs a new Lean proof of model/count correspondence
and independent benchmark comparison with modern CDCL and the original
CNF. No P-vs-NP resolution, fast SAT algorithm, or OpenAI ETH theorem
reproduction is claimed.
