# Operator Frontier

The operator frontier is a planning diagnostic. It records formulas that remain
`NO_COLLAPSE_FOUND` under a selected grammar and suggests candidate operators
that may be worth formalizing later.

It does not solve those formulas. It does not prove that a suggested operator
is necessary. It does not rerun an external SAT solver.

## Candidate Signals

- Pigeonhole rows suggest cardinality or matching-style structure.
- High Horn-clause ratios suggest a Horn terminal class may be useful.
- Clause groups above the exact-XOR `max_k` cap can suggest future larger
  exact-XOR experiments, but an over-cap group is not itself a detection claim.
- Remaining no-collapse rows may motivate a bounded backdoor diagnostic, but
  only with strict caps and certificate replay.

## Boundary

The frontier report is research triage. It is useful for deciding which
operator to build next, not for making benchmark or complexity claims.
