# Symmetry / Orbit Collapse

v2.1 introduces `SYNTACTIC_ORBIT_DIAGNOSTIC`, a deterministic signal extractor
for repeated structure in CNF formulas.

## What It Does

The diagnostic builds variable signatures from:

- positive and negative occurrence counts
- signed clause-width distributions
- co-occurrence fingerprints

Variables with identical signatures are grouped as candidate orbits. Large
candidate orbits in pigeonhole, graph-coloring, clique, or symmetric toy
families are evidence that a future symmetry operator may be useful.

## What It Does Not Do

This is not full graph automorphism detection. It does not compute a certified
group action. It does not add symmetry-breaking clauses. It does not quotient
the formula. It does not certify a new collapse path.

## Breakthrough Target

The target operator is a future `SYMMETRY_ORBIT` collapse route with:

- deterministic orbit discovery
- a sound quotient or symmetry-breaking rule
- witness reconstruction for SAT rows
- proof preservation or external proof checking for UNSAT rows
- independent replay of the symmetry trace

Until those obligations are met, v2.1 reports symmetry as obstruction evidence
only.

## Adversarial Near-Symmetry

The lab includes near-symmetric fixtures where one variable is intentionally
distinguished. The diagnostic must not merge that variable into the symmetric
orbit. This protects the operator frontier from treating superficial repetition
as certified equivalence.
