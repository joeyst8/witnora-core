# TC-063 Affine Component Soundness Lemma

Status: `PROOF_OBLIGATION_REMAINS`

For every residual component accepted as exact affine, the G5 affine
certificate soundly certifies SAT or UNSAT for that component.

Proof obligations:

- Treat G5 checker soundness as an explicit dependency.
- Verify exact affine extraction.
- Reject polluted or incomplete affine components.
- Check SAT component witnesses.
- Check affine UNSAT contradictions.

This lemma is not fully discharged in v2.23 because it depends on G5 affine
checker soundness and future external formalization.
