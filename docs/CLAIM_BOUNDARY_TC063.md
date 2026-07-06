# TC-063 Claim Boundary

Allowed wording:

- `TC-063` is hardened to `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`.
- TC-063 is restricted to `SAF(c,r)`.
- Polynomiality is only for fixed separator bound `c`.
- G5 affine checker soundness is an explicit dependency.
- Native separator-affine certificates are Witnora-native, not external proofs.
- Scaling tests support implementation only.

Forbidden wording:

- `THEOREM_PROVEN_UNQUALIFIED`.
- P vs NP progress.
- Polynomial-time SAT for arbitrary formulas.
- All SAT or hierarchy completeness.
- DRAT/LRAT/FRAT proof unless externally exported and checked.
- HARD or UNKNOWN accepted statuses.

Reason:

TC-063 still has proof obligations and checker-soundness dependencies. v2.23
hardens the theorem shape and review surface without overstating the result.
