# Auxiliary clause-violation tensor bridge: exact semantics, not yet fast counting

**Witnora research checkpoint — 2026-11-03, draft PR #121**

This follows [geometry-aware parity and the direct-scope no-go theorem](GEOMETRY_AWARE_PARITY_FRONTIER.md).
It answers a specific experimental question: can we represent sparse
parity checks **without** merging all their clauses' original variables
into one high-arity factor?

## Factorization

For a source CNF F = ∧_j C_j on source bits x, introduce a fresh
violation bit v_j and the local deterministic factor

    L_j(x_scope(C_j), v_j) = 1  iff  v_j = 1[C_j(x) = false].

For each parity row R, introduce

    P_R(v_R) = 1  iff  XOR_(j in R) v_j = 0.

These are genuine local scopes: for 3-CNF, each L_j touches at most
three original variables plus one auxiliary bit; each P_R touches
at most max_row_width violation bits. The source CNF can still have
large global contraction width, however.

The weighted partition function is

    Z_H(t) = ∑_(x,v) (∏_j L_j(x,v_j)) (∏_R P_R(v_R)) t^(∑_j v_j).

Every source assignment x has a *unique* compatible auxiliary vector
v(x), so equivalently Z_H(t) sums t^(#violated clauses) over source
assignments that pass the sparse parity sketch.

### Exact, unconditional counting identity

    [t^0] Z_H(t) = #SAT(F).

The constant term counts only v=0, which is equivalent to **every**
source clause being satisfied; all such zero vectors pass any parity
rows. Crucially, even when the sketch admits positive-weight
collisions, they cannot affect the constant coefficient.

This is an **algebraic identity**, not an algorithmic breakthrough:
naively extracting one coefficient via interpolation may require
m+1 exact evaluations and each contraction can still be exponential.
Evaluating at t=0 directly recovers the original constraints, so
there is no speedup from this identity alone. Speed improvements
would need elimination orders, cancellations, shared summaries or
other nontrivial exact algorithms.

## Formal trust boundary

The new `formal/Witnora/AuxViolationBridge.lean` theorem
`source_model_iff_unique_exact_aux` connects every satisfying
assignment to exactly one zero-violation auxiliary extension,
with any parity rows included.

The companion `relaxed_aux_iff_parity_acceptance` distinguishes the
relaxed parity-only condition from actual CNF satisfaction.
Unlike a misleading declaration that a sparse sketch is exact,
this bridge preserves the difference explicitly.

The Python prototype `witnora_core/aux_violation_tensors.py`
constructs factor *scopes* and independently evaluates finite
test coefficient profiles for up to fourteen source variables.
The finite enumerator is a TEST ORACLE, not the proposed scalable
tensor counter. `scripts/benchmark_aux_violation_tensors.py`
measures an explicit min-degree elimination-width heuristic on
source, flattened parity and auxiliary factorizations at 32/224,
96/576 and 256/1536. This is not runtime measurement of tensor
contraction or a solver comparison.

## Structural warning

The local clause factor L_j still places every pair of source variables
appearing together in C_j within a common factor. Thus the source primal
graph embeds as a subgraph of this particular auxiliary graph as well.
The representation may **avoid new long-range source-variable couplings**
from flattened parity factors, but it cannot magically beat the source
primal treewidth by the same direct graph-theoretic argument.
Its larger graph may make generic elimination slower.

## Honest next experiment

We need a genuinely structured contraction strategy that can exploit
parity linearity before generic variable elimination; otherwise the
auxiliary construction is only a semantics-preserving intermediate
representation. Benchmark *actual* counting or coefficient computation
(including preprocessing time, runtime and peak memory) versus
direct CNF factor elimination and independently sourced CDCL/model
counting solvers. No polynomial-time SAT, general exact sparse-sketch
equivalence, or P versus NP claim is established.
