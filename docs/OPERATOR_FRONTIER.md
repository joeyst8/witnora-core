# Operator Frontier

The operator frontier is a planning diagnostic. It records formulas that remain
`NO_COLLAPSE_FOUND` under a selected grammar and suggests candidate operators
that may be worth formalizing later.

It does not solve those formulas. It does not prove that a suggested operator
is necessary. It does not rerun an external SAT solver.

## Candidate Signals

- Pigeonhole rows suggest cardinality or matching-style structure.
- Pigeonhole and graph-coloring rows may also expose large deterministic
  syntactic candidate orbits. In v2.1 this is only orbit evidence; it is not a
  certified quotient transformation.
- v2.2 adds exact automorphism certificates for supported small symmetry rows.
  That still does not imply a general quotient rule or pigeonhole collapse.
- High Horn-clause ratios suggest a Horn terminal class may be useful.
- Clause groups above the exact-XOR `max_k` cap can suggest future larger
  exact-XOR experiments, but an over-cap group is not itself a detection claim.
- Remaining no-collapse rows may motivate a bounded backdoor diagnostic, but
  only with strict caps and certificate replay.

## v2.1 Discovery Rankings

`python -m witnora_core.collapse_theory discover-operators` runs the selected
base grammar, collects bounded non-collapse rows, records obstruction
signatures, and ranks candidate next operators. The ranking is a research
planning heuristic. It is not a theorem and it does not certify that the
recommended operator will collapse the family.

The default candidate vocabulary is:

- `SYMMETRY_ORBIT`
- `HIGHER_ARITY_XOR`
- `CARDINALITY_PB`
- `HORN_RENAMABLE`
- `BACKDOOR_TO_TRACTABLE`
- `GRAPH_DECOMPOSITION`

## Boundary

The frontier report is research triage. It is useful for deciding which
operator to build next, not for making benchmark or complexity claims.

## v2.2 Frontier Update

The next frontier split is now explicit:

- graph-coloring toy rows can carry native symmetry certificates and direct SAT
  witness reconstruction;
- pigeonhole rows carry exact orbit and cardinality/PB diagnostics only;
- a future operator must combine symmetry preservation with cardinality/PB
  reasoning before any pigeonhole collapse claim is allowed.
