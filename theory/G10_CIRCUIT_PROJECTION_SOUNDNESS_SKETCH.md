# G10 Circuit Projection Soundness Candidate

Status: `FORMAL_PROOF_SKETCH`

This is a formal proof sketch and proof-obligation record, not a proven theorem.

## Statement

If each projected auxiliary variable has an exact verified definitional gate encoding, projection steps are equisatisfiability-preserving, unsafe auxiliary uses are rejected, and the lifted assignment satisfies the original CNF directly, then SAT witness lift is sound; for UNSAT, if the projected core is UNSAT and every projection step is equisatisfiability-preserving, then original UNSAT is soundly preserved for supported exact definitional families.

## Assumptions

- Only exact AND, OR, and NOT definitions are accepted in the v2.17 prototype.
- Incomplete, polluted, and unsafe auxiliary definitions are rejected.
- SAT lift is checked directly against the original CNF.
- UNSAT requires an equisatisfiability-preserving projection chain.
- No arbitrary auxiliary projection is trusted.

## Proof Sketch

For each verified gate definition, the auxiliary value is forced to equal the gate function on its inputs. SAT lifting evaluates these definitions and then relies on direct CNF satisfaction. UNSAT preservation follows only when every elimination step is certified as equisatisfiable, allowing contradiction in the core to lift back to the original.

## Proof Obligations

- Formalize exact definitional encodings for supported gates.
- Formalize safe-use constraints for projected auxiliary variables.
- Mechanize equisatisfiability of supported projection steps.

## Nonclaims

- Does not claim arbitrary circuit projection.
- Does not claim circuit-SAT solving.
- Does not claim a proven theorem.
- Does not claim P vs NP progress.
