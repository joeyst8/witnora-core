# TC-063 Hardened Bounded Separator-Affine Theorem

Status: `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`

TC-063 states that for fixed constants `c` and supported affine extraction
bound `r`, every `F in SAF(c,r)` can be recognized, collapsed, certified, and
checked by enumerating separator assignments and solving exact affine residual
components through G5.

The theorem remains restricted to `SAF(c,r)`. It does not prove P vs NP, all
SAT, hierarchy completeness, polynomial-time SAT for arbitrary formulas, or an
external DRAT/LRAT/FRAT proof.

The hardened proof is decomposed into eight lemmas:

1. Separator Decomposition.
2. Separator Assignment Exhaustiveness.
3. Affine Component Soundness.
4. SAT Lifting.
5. UNSAT Cover.
6. Polynomial Bound.
7. Native Certificate Boundary.
8. Restricted Scope.

The proof obligations remain explicit. G5 affine checker soundness and native
checker soundness are dependencies rather than hidden assumptions.

## v2.24 External Review Boundary

The v2.24 package republishes TC-063 as the restricted theorem appendix for
external review. It keeps the status
`RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS` and does not upgrade TC-063 to
`THEOREM_PROVEN_UNQUALIFIED`.

The review framing is explicit: the theorem is restricted to `SAF(c,r)`,
polynomiality is only for fixed `c`, the exponential dependence on `c` is
disclosed, G5 affine soundness is a dependency, native certificates are not
external proofs, and finite tests do not substitute for proof.
