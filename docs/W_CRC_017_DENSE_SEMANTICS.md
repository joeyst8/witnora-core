# W-CRC-017: Equal complete variable graphs, different source semantics

Status: **16/16 exact source counts**, with independent Ganak agreement on
all cases and 12/12 analytic-count confirmations, from the verified
completion-driven research queue. The full W-CRC regression CI is a
separate gate.

Dedicated queue run and raw experiment logs:
https://github.com/joeyst8/witnora-core/actions/runs/41724585736

## Question and design

Does the *unweighted source-primal graph* (variable adjacency only)
identify the important difficulty of exact source counting? Test a
strong negative control: make the primal graph exactly **K_n** in
four different signed 2-CNF families, for n=8,16,32,64. The same
n-vertex complete graph has **n(n-1)/2 edges** in every case:

1. **Consistent pairwise XOR parity:** for every vertex pair u,v,
   two CNF clauses encode x_u XOR x_v = p_u XOR p_v, for seeded
   polarity p. There are exactly **2** models: p and its bitwise
   complement. There are n(n-1) clauses.
2. **Inconsistent pairwise XOR parity:** flip the required parity on
   the pair (1,n), while leaving other pair constraints unchanged.
   A contradictory triangle produces exactly **0** models. There
   are n(n-1) clauses.
3. **Positive pairwise OR:** every pair has the clause (x_u OR x_v).
   At most one variable can be false; exactly **n+1** assignments
   satisfy it. There are n(n-1)/2 clauses.
4. **Seeded signed pairwise OR:** every pair has one clause with a
   seeded sign on its first literal; the second stays positive, so
   all-ones remains a witness. No assumed closed-form count.
   There are n(n-1)/2 clauses.

All families have exactly the *same adjacency graph*, but do not
have the same number of clauses, sign profiles, number of solutions,
or algebraic structure. The design falsifies a graph-only metric
as a sufficient semantic description; it does **not** compare
instances controlled for every other syntactic feature.

Witnora's existing exact source adapter extracts the **complete
canonical binary XOR blocks**, uses ordinary affine elimination
for the parity rows, and invokes the existing coherent
orbit/cardinality oracle on the positive-OR cases. The mixed-sign
cases fall to bounded memoized Shannon counting. These are
**known techniques**, not newly devised polynomial-time algorithms.

All results are real source-CNF #SAT counts, not SAT-decision
predictions or estimates; resource limit failures would be reported
as incomplete. Controls at n=5,8 also use exhaustive enumeration
and assert every graph edge exists.

## Results from dedicated GitHub queue

All 16 Witnora counts were exact and matched independently executed
Ganak 2.8.0. Every one of the 12 analytic families/sizes matched
its closed form.

| Variables | Complete graph edges | Consistent XOR | Inconsistent XOR | Positive OR | Signed OR |
|---:|---:|---:|---:|---:|---:|
| 8 | 28 | 2 | 0 | 9 | 4 |
| 16 | 120 | 2 | 0 | 17 | 4 |
| 32 | 496 | 2 | 0 | 33 | 5 |
| 64 | 2016 | 2 | 0 | 65 | 4 |

Exact-source counting time from the single hosted-runner pilot,
**milliseconds; two Witnora repeats, one Ganak invocation per case**:

| n=64 family | Witnora full source count | Ganak engine | W-CRC/Ganak engine ratio |
|---|---:|---:|---:|
| Consistent XOR | 33.8905 | 21.1228 | 1.604 |
| Inconsistent XOR | 33.2044 | 6.5413 | 5.076 |
| Positive OR | 21.5294 | 790.4260 | 0.027 |
| Signed OR | 170.5408 | 9.2352 | 18.466 |

**Important negative result:** graph-equivalent mixed-sign dense 2-CNF
was **~18.5x slower than Ganak** at n=64, despite returning the right
integer count. On the favorable positive-OR case the orbit shortcut
was ~36.7x faster. The time disparities reflect algorithm matching,
CNF encoding and implementation overhead; they are not a statistically
reliable ranking or evidence of hardness separation.

The dedicated read-only task queue executed, in order:
`wcrc016_heldout_unit` PASS,
`wcrc017_dense_unit` PASS,
`wcrc017_dense_ganak` PASS
(last measured task 2.077 seconds). Its JSON artifact was uploaded.
Intentional mocked failures appearing in preceding queue safety tests
are not actual benchmark failures.

## Scientific inference

Graph connectivity alone cannot determine solution count or explain
the availability of short algebraic/symmetry certificates. The
opposite extreme also matters: a complete primal graph can come
from **easy affine consistency checks**, while another formula
with the same adjacency needs a different counting method.

This is an illustrative **controlled counterexample to a
graph-only heuristic**, not a new theorem of complexity theory.
The study does not measure semantic independence or establish a new
interaction invariant. It is unsurprising under known affine
Gaussian elimination, orbit/cardinality identities, and Shannon
decomposition; these are prior art. Dense graphs do not by themselves
prove #SAT hardness.

For a meaningful W-CRC-018 follow-up, formulate and test a
**source-checkable semantic-compression certificate** that predicts
which exact backend succeeds, then challenge it on graph-matched
families with comparable clause counts, width, satisfiability,
model counts where possible, random sign controls, and runtime
budgets. Do not select a family only because the proposed certificate
was hand-built to recognize it. Keep a distinct held-out set and
compare against classical preprocessing baselines.

Source: `scripts/benchmark_crc_dense_semantics.py`.
Tests: `tests/test_crc_dense_semantics.py`.
Research branch: `research/w-crc-001-asymmetric-v1`;
draft PR #122, stacked on TC-063 #121. No TC-063 or Lean theorem
was modified. No general #SAT or P-vs-NP complexity claim follows.
