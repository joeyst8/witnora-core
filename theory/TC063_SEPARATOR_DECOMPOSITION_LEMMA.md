# TC-063 Separator Decomposition Lemma

Status: `FORMALIZED_PROOF_SKETCH`

If `S` is a valid variable separator of the primal graph and `alpha` is a total
assignment to `S`, then after substituting `alpha` into `F`, every residual
clause belongs to exactly one connected component of `F` without `S`, or is
satisfied/removed. No residual clause may span two components.

Proof obligations:

- Reconstruct the primal graph correctly.
- Remove separator variables correctly.
- Substitute separator literals correctly.
- Reject residual cross-component clauses.

This is not an unqualified proven theorem; it is a hardened proof sketch with
test-backed obligations.
