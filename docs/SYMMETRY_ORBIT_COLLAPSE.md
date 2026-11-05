# Symmetry / Orbit Collapse

v2.1 introduced `SYNTACTIC_ORBIT_DIAGNOSTIC`, a deterministic signal extractor
for repeated structure in CNF formulas. v2.2 adds a first certified symmetry
layer for small formulas: exact automorphism validation, orbit certificates,
SBP preservation obligations, and SAT witness reconstruction.

## What It Does

The v2.1 diagnostic builds variable signatures from:

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

## v2.2 Certified Symmetry Layer

`G2_SYMMETRY_CERTIFIED` extends `G1_XOR` with exact automorphism evidence for
supported small formulas. The checker validates that each recorded variable
permutation maps the original CNF clause set exactly onto itself. From these
generators it recomputes variable, literal, and clause orbits.

Supported v2.2 outcomes include:

- `SYMMETRY_NATIVE_CERTIFIED`
- `SYMMETRY_SAT_WITNESS_RECONSTRUCTED`
- `SYMMETRY_DIAGNOSTIC_ONLY`
- `SYMMETRY_CERTIFICATION_FAILED`

DRAT is separate. `SYMMETRY_DRAT_VERIFIED` is allowed only when a proof against
the original CNF is checked by an external checker. v2.2 does not fake such a
claim.

## SBP Preservation Boundary

Symmetry-breaking predicates are generally not implied by the original formula.
They remove symmetric duplicate witnesses. The preservation obligation is:

`F` is satisfiable iff `F and SBP` is satisfiable.

For supported SAT rows, v2.2 checks the native certificate by validating the
automorphisms, recording the SBP as an orbit-representative choice, and
verifying the reconstructed witness against the original CNF. For UNSAT rows,
strengthening by SBP is not enough: an UNSAT symmetry certificate must include a
preservation proof, or a DRAT proof must verify against the original formula.

## Pigeonhole Status

Pigeonhole rows expose exact row/hole automorphisms and cardinality/PB signals.
v2.2 records those signals as battlefield evidence. v2.3 adds a separate native
cardinality/counting certificate for recognized standard `php_n_m` encodings.

Symmetry helps organize the assignment-variable grid and orbit summaries. It
does not by itself prove the contradiction. The UNSAT claim comes from the
native pigeonhole counting certificate.
