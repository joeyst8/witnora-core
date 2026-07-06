# TC-063 UNSAT Cover Lemma

Status: `FORMALIZED_PROOF_SKETCH`

If every `alpha in {0,1}^S` has at least one residual component certified
UNSAT, then `F` is UNSAT.

Proof obligations:

- Cover every separator assignment.
- For each `alpha`, verify at least one affine-UNSAT component.
- Leave no uncovered separator assignment.
- Do not use diagnostic-only components as proof.
