# PR #119: Cost gate for two-clause affine-space branching

Status: **unpromoted exploratory operator; no demonstrated solver win**.

`scripts/experiment_affine_block_branching.py` compares selecting one
unresolved CNF clause versus conjoining two selected clauses in a single
affine-space branching step. Each clause is partitioned according to the
first satisfied literal; the two-clause operator takes disjoint branch
intersections and uses GF(2) elimination to reject inconsistent children.

The operator is mathematically elementary (conjunction/disjoint
case-splitting). No novelty or computational complexity claim is made.

## Synthetic test, not SATLIB

Eight fixed planted synthetic instances at each of 16 and 32 variables;
nine alternating timing repetitions per instance. Candidate search considers
the best six single-clause candidates when choosing a pair.

| Metric | 16 vars, single | 16 vars, pair | 32 vars, single | 32 vars, pair |
| --- | ---: | ---: | ---: | ---: |
| Average surviving models | 204 | 168 | 61,440 | 51,328 |
| Average child branches | 2.50 | 5.50 | 2.625 | 6.25 |
| Average candidate-selection CPU time | 0.2674 ms | 0.7971 ms | 0.8616 ms | 1.7355 ms |

Pairs reduce surviving affine assignments more in a single step, but
**create more than twice as many children** and take roughly **2–3×**
the candidate-selection time. This does not include the cost of solving
all resulting children, so the observed extra pruning does not prove
faster SAT solving. Neither size is the original SATLIB parity benchmark.

`tests/test_affine_block_branching.py` independently checks that pair
branches cover every satisfying assignment **exactly once** on 220 random
small instances, with an exhaustive Boolean oracle, plus deterministic
and monotonicity controls.

## Decision

Do not promote the pair operator. Seek selective operators whose candidate
tests reject large inconsistent affine regions while keeping the branch
frontier and total CPU cost under control. Retain this experiment as a
negative control before any future comparison with native SAT solvers.
