# v2.22 Claim Boundary

v2.23 carries this boundary forward for TC-063 hardening. The updated allowed
status is `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`; the forbidden status
remains `THEOREM_PROVEN_UNQUALIFIED`.

Allowed wording:

- Restricted family theorem for `SAF(c,r)`.
- Polynomial for fixed separator bound `c` and supported affine extraction
  bound `r`.
- SAT requires one all-SAT separator assignment.
- UNSAT requires complete separator-assignment cover.
- Native separator-affine certificates are checked by Witnora.
- Finite n tests support implementation only.

Forbidden wording:

- P vs NP progress.
- Polynomial-time SAT for arbitrary formulas.
- All SAT or all separator formulas.
- Hierarchy completeness.
- DRAT proof unless externally checked.
- Unqualified theorem-proven claim.
- HARD or UNKNOWN accepted statuses.

Reason:

`SAF(c,r)` is intentionally narrow. The scalable statement comes from the
family definition and proof sketch. The finite tests only exercise generators,
checkers, and controls.
