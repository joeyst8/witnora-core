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

v2.24 preserves this boundary in the external review package. It does not claim
P vs NP progress, all-SAT coverage, hierarchy completeness, an unqualified
theorem-proven status, or DRAT/LRAT/FRAT proof status. It asks reviewers to
attack the restricted `SAF(c,r)` theorem, its G5 dependency, and its native
certificate assumptions directly.

v2.25 keeps the same TC-063 boundary in the public preprint: TC-063 is a
restricted theorem with proof obligations over `SAF(c,r)`, not a fully proven
unqualified theorem, not all-SAT coverage, and not P-vs-NP progress.

v2.26 keeps the boundary unchanged while finalizing the public submission
packet. Bibliography hardening and release checklists do not upgrade TC-063:
the status remains `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`, polynomiality
remains only for fixed `c`, and native certificates remain native-only unless
externally exported and checked.
