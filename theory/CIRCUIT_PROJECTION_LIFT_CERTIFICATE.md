# Circuit Projection Lift Certificate

The v2.17 circuit-projection certificate is a native certificate object for
`G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE`.

## Certificate Shape

`CircuitProjectionLiftCertificate` records:

- original formula hash
- projected core formula hash
- projected auxiliary variables
- base variables
- exact gate definitions
- projection steps
- core certificate
- SAT lift or UNSAT lift evidence
- optional orchestration trace
- checker status
- public category
- claim boundary

## Gate Obligations

Each projected variable must have exactly one verified definition. The checker
recomputes AND, OR, NOT, and bounded exact XOR encodings against the original
CNF clauses. Missing clauses reject the certificate.

## Projection Obligations

The checker removes only verified definition clauses. After a projection step,
the projected variable must no longer occur in the remaining formula. This
guards against unsafe auxiliary use.

The final projected core hash must match the certificate.

## SAT Soundness Sketch

If the core assignment satisfies the projected core, every projected gate is
evaluated consistently, and the lifted full assignment satisfies the original
CNF directly, then the SAT witness is sound for the original formula.

## UNSAT Soundness Sketch

If every projection step is equisatisfiability-preserving and the projected
core has a verified native UNSAT certificate, then the original CNF is UNSAT for
the supported exact definitional row.

## Non-Claims

This is a native certificate, not DRAT. It is not a proof of a general circuit
theorem, not a complete circuit-SAT method, not arbitrary auxiliary projection,
and not a P-vs-NP result.
